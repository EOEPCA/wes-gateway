"""Namespace-aware WES gateway. Execution is delegated over HTTP to registered WES services."""

import base64
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import PurePosixPath
from urllib.parse import quote

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.formparsers import MultiPartException

from .artifacts import fetch, rewrite
from .backend import BackendClient
from .config import load_registry
from .models import RunRequest
from .store import RunStore

logger = logging.getLogger(__name__)
NAMESPACE_TAG = "gateway.namespace"
RUN_TAG = "gateway.run_id"
BACKEND_TAG = "gateway.backend"


def error(status, message, **extra):
    return JSONResponse(
        {"msg": message, "status_code": status, **extra}, status_code=status
    )


class UploadLimit:
    """Bound streaming uploads without buffering the whole request body."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        limit = scope["app"].state.registry.max_upload_bytes
        length = dict(scope["headers"]).get(b"content-length")
        if length:
            try:
                if int(length) < 0 or int(length) > limit:
                    return await error(413, "Request exceeds configured upload limit")(
                        scope, receive, send
                    )
            except ValueError:
                return await error(400, "Invalid Content-Length")(scope, receive, send)
        total = 0

        async def limited_receive():
            nonlocal total
            message = await receive()
            total += len(message.get("body", b""))
            if total > limit:
                scope["upload_exceeded"] = True
                # The multipart parser closes its temporary files on this exception.
                raise MultiPartException("Request exceeds configured upload limit")
            return message

        await self.app(scope, limited_receive, send)


def create_app(registry=None, database_url=None, transport=None):
    @asynccontextmanager
    async def lifespan(app):
        config = registry or load_registry(
            os.environ.get("WES_BACKENDS_CONFIG", "config/backends.yaml")
        )
        config.check_secrets()
        store = RunStore(
            database_url
            or os.environ.get("WES_DATABASE_URL", "sqlite:///./wes-gateway.db")
        )
        clients = {}
        try:
            store.validate_bindings(config)
            clients = {
                key: BackendClient(value, transport=transport)
                for key, value in config.backends.items()
            }
            app.state.registry, app.state.store, app.state.clients = (
                config,
                store,
                clients,
            )
            yield
        finally:
            for client in clients.values():
                await client.close()
            store.close()

    app = FastAPI(
        title="Workflow Execution Service",
        version="1.1.0",
        lifespan=lifespan,
        description="Namespace-aware gateway; backend service-info reports supported WES versions.",
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        if request.scope.get("upload_exceeded"):
            return error(413, "Request exceeds configured upload limit")
        return error(exc.status_code, str(exc.detail))

    @app.exception_handler(MultiPartException)
    async def multipart_error(request, exc):
        return error(413 if request.scope.get("upload_exceeded") else 400, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        fields = ", ".join(".".join(map(str, item["loc"])) for item in exc.errors())
        return error(400, "Invalid request fields: " + fields)

    @app.exception_handler(SQLAlchemyError)
    async def storage_error(request, exc):
        logger.error("Run metadata storage operation failed (%s)", type(exc).__name__)
        return error(503, "Run metadata storage is unavailable")

    app.add_middleware(UploadLimit)

    def resolve(namespace):
        ns = app.state.registry.namespaces.get(namespace)
        if ns is None:
            raise HTTPException(404, "Unknown WES namespace")
        return ns.backend, app.state.clients[ns.backend]

    def resolve_run(namespace, run_id):
        resolve(namespace)
        row = app.state.store.get(namespace, run_id)
        if row is None or row["phase"] == "REJECTED":
            raise HTTPException(404, "Run not found in namespace")
        return row, app.state.clients[row["backend"]]

    def path(run, suffix=""):
        return "/runs/" + quote(run["upstream_id"], safe="") + suffix

    def tags(run):
        return {
            NAMESPACE_TAG: run["namespace"],
            RUN_TAG: run["id"],
            BACKEND_TAG: run["backend"],
        }

    def forwarded(response, payload):
        headers = {
            k: v
            for k, v in response.headers.items()
            if k.lower() in {"retry-after", "www-authenticate"}
        }
        return JSONResponse(payload, status_code=response.status_code, headers=headers)

    router = APIRouter(prefix="/wes/v1/{namespace}")

    @app.get("/healthz", include_in_schema=False)
    async def health():
        return {"status": "ok"}

    @app.get("/readyz", include_in_schema=False)
    async def ready():
        app.state.store.page("", 0, 1)
        return {"status": "ready"}

    @router.get("/service-info")
    async def service_info(namespace: str):
        _, client = resolve(namespace)
        response, payload = await client.json("GET", "/service-info")
        if response.is_success:
            # Toil reports --setEnv defaults including deployment credentials.
            payload["default_workflow_engine_parameters"] = [
                item
                for item in payload.get("default_workflow_engine_parameters", [])
                if item.get("name") != "--setEnv"
            ]
        return forwarded(response, payload)

    submission_schema = {
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": [
                            "workflow_url",
                            "workflow_type",
                            "workflow_type_version",
                            "workflow_params",
                        ],
                        "properties": {
                            **{
                                name: {"type": "string"}
                                for name in RunRequest.model_fields
                            },
                            "workflow_attachment": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                            },
                        },
                    }
                }
            },
        }
    }

    @router.post("/runs", openapi_extra=submission_schema)
    async def submit(namespace: str, request: Request):
        backend_id, client = resolve(namespace)
        async with request.form(
            max_files=100,
            max_fields=100,
            max_part_size=app.state.registry.max_upload_bytes,
        ) as form:
            data, files = {}, []
            for key, value in form.multi_items():
                if key == "workflow_attachment" and isinstance(value, UploadFile):
                    filename = value.filename or ""
                    if (
                        not filename
                        or "\\" in filename
                        or PurePosixPath(filename).is_absolute()
                        or ".." in PurePosixPath(filename).parts
                    ):
                        raise HTTPException(
                            400, "Attachment filenames must be safe relative paths"
                        )
                    if any(part[1][0] == filename for part in files):
                        raise HTTPException(400, "Duplicate attachment filename")
                    files.append(
                        (key, (value.filename, value.file, value.content_type))
                    )
                elif key in RunRequest.model_fields and isinstance(value, str):
                    if key in data:
                        raise HTTPException(400, f"Duplicate submission field: {key}")
                    data[key] = value
                else:
                    raise HTTPException(400, "Unsupported submission field")
            for name in ("workflow_params", "tags", "workflow_engine_parameters"):
                if name in data:
                    try:
                        data[name] = json.loads(data[name])
                    except ValueError:
                        raise HTTPException(
                            400, f"{name} must be a JSON object"
                        ) from None
                    if not isinstance(data[name], dict):
                        raise HTTPException(400, f"{name} must be a JSON object")
            if "workflow_params" not in data:
                raise HTTPException(400, "Missing workflow_params")
            try:
                validated = RunRequest.model_validate(data)
            except ValidationError:
                raise HTTPException(400, "Invalid WES submission fields") from None
            if (
                not validated.workflow_url
                or not validated.workflow_type
                or not validated.workflow_type_version
            ):
                raise HTTPException(400, "Workflow identity fields must not be empty")
            if validated.workflow_engine_version and not validated.workflow_engine:
                raise HTTPException(
                    400, "workflow_engine_version requires workflow_engine"
                )
            run = app.state.store.create(namespace, backend_id, client.config.identity)
            data["tags"] = {**data.get("tags", {}), **tags(run)}
            parts = [
                (name, (None, json.dumps(value) if isinstance(value, dict) else value))
                for name, value in data.items()
            ]
            try:
                response, payload = await client.json(
                    "POST", "/runs", files=parts + files
                )
                if response.is_success:
                    upstream_id = payload.get("run_id")
                    if not isinstance(upstream_id, str) or not upstream_id:
                        raise HTTPException(502, "WES backend returned no run ID")
                    app.state.store.accepted(run["id"], upstream_id)
                    return forwarded(response, {**payload, "run_id": run["id"]})
                app.state.store.phase(
                    run["id"],
                    "REJECTED" if 400 <= response.status_code < 500 else "UNKNOWN",
                )
                return forwarded(response, {**payload, "gateway_run_id": run["id"]})
            except (HTTPException, SQLAlchemyError) as exc:
                # A durable SUBMITTING record and reserved tag enable operator reconciliation
                # even when the upstream succeeded and the final database update failed.
                logger.error(
                    "Submission outcome needs reconciliation: gateway run %s (%s)",
                    run["id"],
                    type(exc).__name__,
                )
                status = exc.status_code if isinstance(exc, HTTPException) else 503
                return error(
                    status,
                    "Submission outcome is unknown; do not resubmit. Reconcile this gateway run ID.",
                    gateway_run_id=run["id"],
                )

    @router.get("/runs/{run_id}/status")
    async def status(namespace: str, run_id: str):
        run, client = resolve_run(namespace, run_id)
        if not run["upstream_id"]:
            return {"run_id": run_id, "state": "UNKNOWN"}
        response, payload = await client.json("GET", path(run, "/status"))
        if response.is_success:
            if not isinstance(payload.get("state"), str):
                raise HTTPException(502, "WES backend returned no run state")
            payload["run_id"] = run_id
        return forwarded(response, payload)

    @router.get("/runs")
    async def list_runs(
        namespace: str,
        page_size: int = Query(default=100, ge=1, le=1000),
        page_token: str | None = None,
    ):
        resolve(namespace)
        after = 0
        if page_token:
            try:
                token_namespace, after = json.loads(
                    base64.urlsafe_b64decode(page_token).decode()
                )
                if token_namespace != namespace or type(after) is not int or after < 0:
                    raise ValueError()
            except (ValueError, TypeError, UnicodeError):
                raise HTTPException(400, "Invalid page token for namespace") from None
        rows = app.state.store.page(namespace, after, page_size + 1)
        workflows = []
        for run in rows[:page_size]:
            state = "UNKNOWN"
            if run["upstream_id"]:
                client = app.state.clients[run["backend"]]
                response, payload = await client.json("GET", path(run, "/status"))
                if not response.is_success:
                    return forwarded(response, payload)
                state = payload.get("state", "UNKNOWN")
            workflows.append({"run_id": run["id"], "state": state, "tags": tags(run)})
        next_token = (
            base64.urlsafe_b64encode(
                json.dumps([namespace, rows[page_size - 1]["seq"]]).encode()
            ).decode()
            if len(rows) > page_size
            else ""
        )
        return {"workflows": workflows, "next_page_token": next_token}

    @router.get("/runs/{run_id}")
    async def detail(namespace: str, run_id: str, request: Request):
        run, client = resolve_run(namespace, run_id)
        if not run["upstream_id"]:
            return {
                "run_id": run_id,
                "state": "UNKNOWN",
                "request": {"tags": tags(run)},
                "run_log": {
                    "system_logs": [
                        "Submission requires operator reconciliation; do not resubmit."
                    ]
                },
            }
        response, payload = await client.json("GET", path(run))
        if response.is_success:
            payload["run_id"] = run_id
            original = payload.get("request") or {}
            original["tags"] = {**(original.get("tags") or {}), **tags(run)}
            payload["request"] = original
            payload = rewrite(payload, request, run, client.config, app.state.store)
        return forwarded(response, payload)

    @router.post("/runs/{run_id}/cancel")
    async def cancel(namespace: str, run_id: str):
        run, client = resolve_run(namespace, run_id)
        if not run["upstream_id"]:
            raise HTTPException(409, "Reconcile the submission before cancelling")
        response, payload = await client.json("POST", path(run, "/cancel"))
        if response.is_success:
            payload["run_id"] = run_id
        return forwarded(response, payload)

    @router.get("/runs/{run_id}/tasks", name="list_tasks")
    async def list_tasks(
        namespace: str,
        run_id: str,
        request: Request,
        page_size: int | None = Query(default=None, ge=1),
        page_token: str | None = None,
    ):
        run, client = resolve_run(namespace, run_id)
        if not run["upstream_id"]:
            raise HTTPException(409, "Reconcile the submission before retrieving tasks")
        params = {
            k: v
            for k, v in {"page_size": page_size, "page_token": page_token}.items()
            if v is not None
        }
        response, payload = await client.json("GET", path(run, "/tasks"), params=params)
        if response.is_success:
            payload = rewrite(payload, request, run, client.config, app.state.store)
        return forwarded(response, payload)

    @router.get("/runs/{run_id}/tasks/{task_id}")
    async def task(namespace: str, run_id: str, task_id: str, request: Request):
        run, client = resolve_run(namespace, run_id)
        if not run["upstream_id"]:
            raise HTTPException(409, "Reconcile the submission before retrieving tasks")
        response, payload = await client.json(
            "GET", path(run, "/tasks/" + quote(task_id, safe=""))
        )
        if response.is_success:
            payload = rewrite(payload, request, run, client.config, app.state.store)
        return forwarded(response, payload)

    @router.get("/runs/{run_id}/artifacts/{token}", name="get_artifact")
    async def get_artifact(namespace: str, run_id: str, token: str, request: Request):
        run, client = resolve_run(namespace, run_id)
        uri = app.state.store.artifact(token, run_id)
        if uri is None:
            raise HTTPException(404, "Artifact not found for run")
        return await fetch(uri, client, request, run, app.state.store)

    app.include_router(router)

    @app.api_route(
        "/runs{suffix:path}", methods=["GET", "POST"], include_in_schema=False
    )
    @app.api_route("/service-info", methods=["GET"], include_in_schema=False)
    @app.api_route(
        "/ga4gh/wes/v1/{legacy_path:path}",
        methods=["GET", "POST"],
        include_in_schema=False,
    )
    async def legacy(request: Request, suffix: str = "", legacy_path: str = ""):
        default = app.state.registry.default_namespace
        if not default:
            raise HTTPException(
                404, "Use /wes/v1/{namespace}; no default namespace is configured"
            )
        from fastapi.responses import RedirectResponse

        resource = legacy_path or request.url.path.lstrip("/")
        url = str(request.base_url).rstrip("/") + f"/wes/v1/{default}/{resource}"
        if request.url.query:
            url += "?" + request.url.query
        return RedirectResponse(url, status_code=307)

    return app


app = create_app()
