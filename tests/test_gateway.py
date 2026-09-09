import json
from email.parser import BytesParser
from email.policy import default

import httpx
import pytest
from fastapi.testclient import TestClient

from wes_api_gateway.config import ConfigurationError, Registry, load_registry
from wes_api_gateway.main import create_app
from wes_api_gateway.store import RunStore


@pytest.fixture
def registry():
    return Registry.model_validate(
        {
            "version": 1,
            "backends": {
                "a": {"base_url": "http://toil-a/ga4gh/wes/v1"},
                "b": {"base_url": "http://toil-b/ga4gh/wes/v1"},
            },
            "namespaces": {
                "alpha": {"backend": "a"},
                "beta": {"backend": "b"},
                "shared": {"backend": "a"},
            },
        }
    )


@pytest.fixture
def upstream():
    calls = []
    submissions = {}

    def handle(request):
        calls.append(request)
        path = request.url.path
        if path.endswith("service-info"):
            return httpx.Response(
                200,
                json={
                    "supported_wes_versions": ["1.0.0"],
                    "workflow_engine_versions": {"toil": "9.4.1"},
                    "default_workflow_engine_parameters": [
                        {"name": "--setEnv", "default_value": "SECRET=value"},
                        {"name": "--batchSystem", "default_value": "kubernetes"},
                    ],
                },
            )
        if request.method == "POST" and path.endswith("/runs"):
            message = BytesParser(policy=default).parsebytes(
                b"Content-Type: "
                + request.headers["content-type"].encode()
                + b"\r\n\r\n"
                + request.content
            )
            parts = list(message.iter_parts())
            data = {
                p.get_param("name", header="content-disposition"): p.get_payload(
                    decode=True
                ).decode()
                for p in parts
                if not p.get_filename()
            }
            # Every backend deliberately returns the same ID; the gateway must disambiguate.
            submissions[request.url.host] = data
            return httpx.Response(200, json={"run_id": "same-id"})
        if path.endswith("/status"):
            return httpx.Response(200, json={"run_id": "same-id", "state": "COMPLETE"})
        if path.endswith("/cancel"):
            return httpx.Response(200, json={"run_id": "same-id"})
        if "/logs/" in path:
            return httpx.Response(
                200,
                stream=httpx.ByteStream(b"hello log\n"),
                headers={"content-type": "text/plain"},
            )
        if path.endswith("/tasks"):
            return httpx.Response(
                200, json={"task_logs": [], "next_page_token": "next"}
            )
        return httpx.Response(
            200,
            json={
                "run_id": "same-id",
                "state": "COMPLETE",
                "request": {"tags": {"user": "test"}},
                "run_log": {"stdout": "../../../../toil/wes/v1/logs/same-id/stdout"},
                "outputs": {"greeting": "hello\n"},
            },
        )

    return handle, calls, submissions


def submit(client, namespace="alpha", **extra):
    return client.post(
        f"/wes/v1/{namespace}/runs",
        data={
            "workflow_type": "CWL",
            "workflow_type_version": "v1.2",
            "workflow_url": "packed.cwl#main",
            "workflow_params": '{"message":"hi"}',
            "tags": '{"gateway.namespace":"spoof","project":"test"}',
            **extra,
        },
        files=[
            ("workflow_attachment", ("packed.cwl", b"cwl body", "text/plain")),
            ("workflow_attachment", ("nested/step.cwl", b"step body", "text/plain")),
        ],
    )


def test_submission_status_details_cancellation_and_artifacts(
    registry, upstream, tmp_path
):
    handle, calls, submissions = upstream
    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(handle)
        )
    ) as client:
        response = submit(client)
        assert response.status_code == 200, response.text
        run_id = response.json()["run_id"]
        assert run_id != "same-id"
        posted = submissions["toil-a"]
        assert posted["workflow_url"] == "packed.cwl#main"
        assert json.loads(posted["workflow_params"]) == {"message": "hi"}
        tags = json.loads(posted["tags"])
        assert tags == {
            "gateway.namespace": "alpha",
            "gateway.run_id": run_id,
            "gateway.backend": "a",
            "project": "test",
        }
        assert b'filename="nested/step.cwl"' in calls[0].content
        assert b"step body" in calls[0].content and b"cwl body" in calls[0].content
        base = f"/wes/v1/alpha/runs/{run_id}"
        assert client.get(base + "/status").json() == {
            "run_id": run_id,
            "state": "COMPLETE",
        }
        detail = client.get(base).json()
        assert detail["outputs"] == {"greeting": "hello\n"}
        assert detail["request"]["tags"]["gateway.namespace"] == "alpha"
        log_url = detail["run_log"]["stdout"]
        assert f"/wes/v1/alpha/runs/{run_id}/artifacts/" in log_url
        assert client.get(log_url).text == "hello log\n"
        assert client.get(log_url.replace("/alpha/", "/beta/")).status_code == 404
        assert client.post(base + "/cancel").json()["run_id"] == run_id
        assert client.get(base + "/tasks?page_size=3&page_token=abc").status_code == 200
        assert str(calls[-1].url.query) == "b'page_size=3&page_token=abc'"
        info = client.get("/wes/v1/alpha/service-info").json()
        assert info["supported_wes_versions"] == ["1.0.0"]
        assert "SECRET" not in json.dumps(info)


def test_namespaces_collisions_listing_and_restart(registry, upstream, tmp_path):
    handle, calls, _ = upstream
    url = f"sqlite:///{tmp_path}/runs.db"
    with TestClient(create_app(registry, url, httpx.MockTransport(handle))) as client:
        a = submit(client).json()["run_id"]
        b = submit(client, "beta").json()["run_id"]
        assert a != b
        assert client.get("/wes/v1/alpha/runs").json()["workflows"][0]["run_id"] == a
        assert client.get("/wes/v1/beta/runs").json()["workflows"][0]["run_id"] == b
        assert client.get("/wes/v1/shared/runs").json()["workflows"] == []
        count = len(calls)
        for suffix, method in [
            ("", client.get),
            ("/status", client.get),
            ("/cancel", client.post),
            ("/tasks", client.get),
        ]:
            assert method(f"/wes/v1/beta/runs/{a}{suffix}").status_code == 404
        assert client.get("/wes/v1/invalid/runs").status_code == 404
        assert client.post("/wes/v1/invalid/runs").status_code == 404
        assert len(calls) == count
    # Remapping affects new submissions, never existing runs. A second process can
    # open the same metadata store; multi-host deployments use PostgreSQL.
    registry.namespaces["alpha"].backend = "b"
    with TestClient(create_app(registry, url, httpx.MockTransport(handle))) as client:
        assert client.get(f"/wes/v1/alpha/runs/{a}/status").status_code == 200
        assert calls[-1].url.host == "toil-a"
        assert client.get(f"/wes/v1/beta/runs/{b}/status").status_code == 200
        assert calls[-1].url.host == "toil-b"
    registry.backends["a"].base_url = "http://changed/wes/v1"
    with (
        pytest.raises(ConfigurationError, match="recorded runs"),
        TestClient(create_app(registry, url)),
    ):
        pass


def test_pagination_scoped_tokens(registry, upstream, tmp_path):
    handle, _, _ = upstream
    url = f"sqlite:///{tmp_path}/runs.db"
    store = RunStore(url)
    one = store.create("alpha", "a", registry.backends["a"].identity)
    two = store.create("alpha", "a", registry.backends["a"].identity)
    store.close()
    with TestClient(create_app(registry, url, httpx.MockTransport(handle))) as client:
        page = client.get("/wes/v1/alpha/runs?page_size=1").json()
        assert page["workflows"][0]["run_id"] == one["id"]
        token = page["next_page_token"]
        page2 = client.get("/wes/v1/alpha/runs", params={"page_token": token}).json()
        assert page2["workflows"][0]["run_id"] == two["id"]
        assert page2["next_page_token"] == ""
        assert (
            client.get("/wes/v1/beta/runs", params={"page_token": token}).status_code
            == 400
        )
        for token in ("broken", "e30=", "bnVsbA==", "W10="):
            assert (
                client.get(
                    "/wes/v1/alpha/runs", params={"page_token": token}
                ).status_code
                == 400
            )
        assert client.get("/wes/v1/alpha/runs?page_size=0").status_code == 400


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("timeout", 504),
        ("offline", 502),
        ("html", 502),
        ("no-id", 502),
        ("rejected", 400),
    ],
)
def test_submission_failures_not_retried(registry, tmp_path, mode, expected):
    calls = []

    def handle(request):
        calls.append(request)
        if mode == "timeout":
            raise httpx.ReadTimeout("private URL", request=request)
        if mode == "offline":
            raise httpx.ConnectError("private URL", request=request)
        if mode == "html":
            return httpx.Response(502, text="private upstream HTML")
        if mode == "rejected":
            return httpx.Response(400, json={"msg": "bad CWL", "status_code": 400})
        return httpx.Response(200, json={})

    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(handle)
        )
    ) as client:
        response = submit(client)
        assert response.status_code == expected
        assert len(calls) == 1
        assert "private" not in response.text
        run_id = response.json()["gateway_run_id"]
        if mode != "rejected":
            assert (
                client.get(f"/wes/v1/alpha/runs/{run_id}/status").json()["state"]
                == "UNKNOWN"
            )
            assert client.post(f"/wes/v1/alpha/runs/{run_id}/cancel").status_code == 409


def test_form_validation_and_url_only_submission(registry, upstream, tmp_path):
    handle, calls, _ = upstream
    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(handle)
        )
    ) as client:
        for fields in (
            {"workflow_params": "bad"},
            {"tags": "[]"},
            {"workflow_type": ""},
            {"workflow_engine_version": "9"},
        ):
            assert submit(client, **fields).status_code == 400
        assert calls == []
        response = client.post(
            "/wes/v1/alpha/runs",
            data={
                "workflow_type": "CWL",
                "workflow_type_version": "v1.2",
                "workflow_url": "https://example.org/test.cwl",
                "workflow_params": "{}",
            },
        )
        assert response.status_code == 200
        assert client.get("/runs").status_code == 404
    registry.default_namespace = "alpha"
    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(handle)
        )
    ) as client:
        assert (
            client.get("/ga4gh/wes/v1/service-info", follow_redirects=False)
            .headers["location"]
            .endswith("/wes/v1/alpha/service-info")
        )


def test_upload_limits(registry, upstream, tmp_path):
    registry.max_upload_bytes = 100
    handle, calls, _ = upstream
    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(handle)
        )
    ) as client:
        assert submit(client).status_code == 413
        response = client.post(
            "/wes/v1/alpha/runs",
            content=iter([b"x" * 101]),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 413, response.text
        assert calls == []


def test_config_errors_and_secret_redaction(tmp_path, monkeypatch):
    path = tmp_path / "registry.yaml"
    for content, message in [
        ("version: 1\nversion: 1", "duplicate"),
        ("version: 2\nbackends: {}\nnamespaces: {}", "version"),
        (
            "version: 1\nbackends: {a: {base_url: 'ftp://example.org'}}\nnamespaces: {n: {backend: a}}",
            "base_url",
        ),
        (
            "version: 1\nbackends: {a: {base_url: 'https://user:secret@example.org'}}\nnamespaces: {n: {backend: a}}",
            "base_url",
        ),
        (
            "version: 1\nbackends: {a: {base_url: 'https://example.org', read_timeout: 0}}\nnamespaces: {n: {backend: a}}",
            "read_timeout",
        ),
        (
            "version: 1\nbackends: {a: {base_url: 'https://example.org', type: missing}}\nnamespaces: {n: {backend: a}}",
            "type",
        ),
        (
            "version: 1\nbackends: {a: {base_url: 'https://example.org', typo: secret}}\nnamespaces: {n: {backend: a}}",
            "typo",
        ),
        (
            "version: 1\nbackends: {a: {base_url: 'https://example.org'}}\nnamespaces: {n: {backend: absent}}",
            "unknown backend",
        ),
    ]:
        path.write_text(content)
        with pytest.raises(ConfigurationError, match=message) as exc:
            load_registry(path)
        assert "secret" not in str(exc.value)
    monkeypatch.delenv("TEST_BACKEND_TOKEN", raising=False)
    path.write_text(
        "version: 1\nbackends: {a: {base_url: 'https://example.org', bearer_token_env: TEST_BACKEND_TOKEN}}\nnamespaces: {n: {backend: a}}"
    )
    with pytest.raises(ConfigurationError, match="TEST_BACKEND_TOKEN"):
        load_registry(path)
    monkeypatch.setenv("TEST_BACKEND_TOKEN", "secret")
    assert load_registry(path).namespaces["n"].backend == "a"


def test_error_status_and_backend_authorization(registry, tmp_path, monkeypatch):
    monkeypatch.setenv("BACKEND_TEST_TOKEN", "upstream-secret")
    registry.backends["a"].bearer_token_env = "BACKEND_TEST_TOKEN"

    def handle(request):
        assert request.headers["authorization"] == "Bearer upstream-secret"
        assert "x-client-secret" not in request.headers
        return httpx.Response(403, json={"msg": "forbidden", "status_code": 403})

    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(handle)
        )
    ) as client:
        response = client.get(
            "/wes/v1/alpha/service-info",
            headers={
                "authorization": "Bearer client-secret",
                "x-client-secret": "value",
            },
        )
        assert response.status_code == 403
        assert response.json() == {"msg": "forbidden", "status_code": 403}


def test_artifact_target_scope_and_redirects(registry, upstream, tmp_path):
    handle, calls, _ = upstream

    def malicious(request):
        if request.url.path.endswith("/runs/same-id"):
            return httpx.Response(
                200,
                json={
                    "state": "COMPLETE",
                    "request": {},
                    "run_log": {
                        "stdout": "http://169.254.169.254/same-id/token",
                        "stderr": "http://toil-a/toil/wes/v1/logs/other-run/stderr",
                    },
                },
            )
        return handle(request)

    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(malicious)
        )
    ) as client:
        run_id = submit(client).json()["run_id"]
        detail = client.get(f"/wes/v1/alpha/runs/{run_id}").json()
        assert detail["run_log"]["stdout"] == "http://169.254.169.254/same-id/token"
        assert (
            client.get(
                f"/wes/v1/alpha/runs/{run_id}/artifacts/not-recorded?url=http://169.254.169.254"
            ).status_code
            == 404
        )
        assert all(request.url.host == "toil-a" for request in calls)

    def redirect(request):
        if "/logs/" in request.url.path:
            return httpx.Response(
                302, headers={"location": "http://169.254.169.254/token"}
            )
        return handle(request)

    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(redirect)
        )
    ) as client:
        log = client.get(f"/wes/v1/alpha/runs/{run_id}").json()["run_log"]["stdout"]
        assert client.get(log).status_code == 502


def test_s3_output_stream_and_request_preservation(
    registry, upstream, tmp_path, monkeypatch
):
    import io

    from botocore.response import StreamingBody

    from wes_api_gateway import artifacts
    from wes_api_gateway.config import S3Settings

    monkeypatch.setenv("S3_TEST_KEY", "key")
    monkeypatch.setenv("S3_TEST_SECRET", "secret")
    registry.backends["a"].s3 = S3Settings(
        access_key_env="S3_TEST_KEY",
        secret_key_env="S3_TEST_SECRET",
        allowed_prefixes=["s3://results/alpha/"],
    )
    handle, _, _ = upstream

    def response(request):
        if request.url.path.endswith("/runs/same-id"):
            return httpx.Response(
                200,
                json={
                    "state": "COMPLETE",
                    "request": {
                        "workflow_params": {"location": "s3://results/alpha/input.txt"}
                    },
                    "outputs": {
                        "file": {
                            "class": "File",
                            "location": "s3://results/alpha/output.txt",
                        },
                        "other": "s3://results/beta/private.txt",
                    },
                },
            )
        return handle(request)

    class S3:
        def __init__(self):
            self.closed = False

        def get_object(self, **kwargs):
            assert kwargs == {
                "Bucket": "results",
                "Key": "alpha/output.txt",
                "Range": "bytes=0-4",
            }
            return {
                "Body": StreamingBody(io.BytesIO(b"hello"), 5),
                "ContentLength": 5,
                "ContentRange": "bytes 0-4/10",
                "ContentType": "text/plain",
            }

        def close(self):
            self.closed = True

    s3 = S3()
    monkeypatch.setattr(artifacts.boto3, "client", lambda *args, **kwargs: s3)
    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(response)
        )
    ) as client:
        run_id = submit(client).json()["run_id"]
        detail = client.get(f"/wes/v1/alpha/runs/{run_id}").json()
        assert (
            detail["request"]["workflow_params"]["location"]
            == "s3://results/alpha/input.txt"
        )
        assert detail["outputs"]["other"] == "s3://results/beta/private.txt"
        url = detail["outputs"]["file"]["location"]
        response = client.get(url, headers={"range": "bytes=0-4"})
        assert response.status_code == 206
        assert response.content == b"hello"
        assert response.headers["content-range"] == "bytes 0-4/10"
        assert s3.closed


def test_failed_recording_can_be_reconciled_without_resubmission(
    registry, tmp_path, monkeypatch
):
    import asyncio

    from sqlalchemy.exc import OperationalError

    from wes_api_gateway import reconcile
    from wes_api_gateway.backend import BackendClient

    url = f"sqlite:///{tmp_path}/runs.db"
    submitted_tags = {}
    submissions = []

    def handle(request):
        if request.method == "POST":
            submissions.append(request)
            message = BytesParser(policy=default).parsebytes(
                b"Content-Type: "
                + request.headers["content-type"].encode()
                + b"\r\n\r\n"
                + request.content
            )
            for part in message.iter_parts():
                if part.get_param("name", header="content-disposition") == "tags":
                    submitted_tags.update(json.loads(part.get_payload(decode=True)))
            return httpx.Response(200, json={"run_id": "upstream-recover"})
        if request.url.path.endswith("/runs"):
            return httpx.Response(
                200,
                json={
                    "workflows": [{"run_id": "upstream-recover"}],
                    "next_page_token": "",
                },
            )
        return httpx.Response(200, json={"request": {"tags": submitted_tags}})

    transport = httpx.MockTransport(handle)
    app = create_app(registry, url, transport)
    with TestClient(app) as client:

        def fail(*args):
            raise OperationalError("record", {}, Exception("unavailable"))

        monkeypatch.setattr(app.state.store, "accepted", fail)
        response = submit(client)
        assert response.status_code == 503
        run_id = response.json()["gateway_run_id"]
        assert app.state.store.get("alpha", run_id)["upstream_id"] is None
    monkeypatch.setenv("WES_DATABASE_URL", url)
    monkeypatch.setattr(reconcile, "load_registry", lambda path: registry)
    monkeypatch.setattr(
        reconcile, "BackendClient", lambda config: BackendClient(config, transport)
    )
    asyncio.run(reconcile.reconcile())
    store = RunStore(url)
    assert store.get("alpha", run_id)["upstream_id"] == "upstream-recover"
    assert len(submissions) == 1
    store.close()


def test_unsafe_attachment_names_are_rejected(registry, upstream, tmp_path):
    handle, calls, _ = upstream
    with TestClient(
        create_app(
            registry, f"sqlite:///{tmp_path}/runs.db", httpx.MockTransport(handle)
        )
    ) as client:
        for name in ("../escape.cwl", "/absolute.cwl", "nested/../../escape.cwl"):
            response = client.post(
                "/wes/v1/alpha/runs",
                data={
                    "workflow_type": "CWL",
                    "workflow_type_version": "v1.2",
                    "workflow_url": name,
                    "workflow_params": "{}",
                },
                files={"workflow_attachment": (name, b"test")},
            )
            assert response.status_code == 400
        assert calls == []
