"""Run-scoped artifact links. Fetch targets come only from recorded backend responses."""

import hashlib
import os
import re
from urllib.parse import quote, unquote, urljoin, urlsplit

import boto3
import httpx
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool


def permitted(uri, backend, upstream_id):
    target, origin = urlsplit(uri), urlsplit(backend.base_url)
    segments = unquote(target.path).split("/")
    if (
        target.fragment
        or target.username
        or target.password
        or any(p in {".", ".."} for p in segments)
    ):
        return False
    if target.scheme in {"http", "https"}:
        return (target.scheme, target.netloc) == (
            origin.scheme,
            origin.netloc,
        ) and upstream_id in segments
    if target.scheme == "s3" and backend.s3:
        return any(uri.startswith(prefix) for prefix in backend.s3.allowed_prefixes)
    return False


def rewrite(payload, request, run, backend, store):
    def link(uri):
        if not urlsplit(uri).scheme:
            uri = urljoin(
                backend.base_url + "/runs/" + quote(run["upstream_id"], safe=""), uri
            )
        if not permitted(uri, backend, run["upstream_id"]):
            return uri
        token = hashlib.sha256((run["id"] + "\0" + uri).encode()).hexdigest()
        store.artifact(token, run["id"], uri)
        return str(
            request.url_for(
                "get_artifact",
                namespace=run["namespace"],
                run_id=run["id"],
                token=token,
            )
        )

    def walk(value, key=None):
        if key == "request":
            return value
        if isinstance(value, dict):
            return {k: walk(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(item, key) for item in value]
        if isinstance(value, str):
            if key == "cmd":
                return re.sub(
                    r"--setEnv(?:=|\s+)(?:\"[^\"]*\"|'[^']*'|\S+)",
                    "--setEnv=[redacted]",
                    value,
                )
            if key == "task_logs_url":
                return str(
                    request.url_for(
                        "list_tasks", namespace=run["namespace"], run_id=run["id"]
                    )
                )
            if key in {"stdout", "stderr", "location"} or (
                key != "workflow_url" and value.startswith("s3://")
            ):
                return link(value)
        return value

    return walk(payload)


async def fetch(uri, backend_client, request, run, store):
    backend = backend_client.config
    if not permitted(uri, backend, run["upstream_id"]):
        raise HTTPException(403, "Artifact is outside the configured backend scope")
    if uri.startswith("s3://"):
        settings = backend.s3
        client = boto3.client(
            "s3",
            endpoint_url=settings.endpoint_url,
            region_name=settings.region,
            aws_access_key_id=os.environ[settings.access_key_env],
            aws_secret_access_key=os.environ[settings.secret_key_env],
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 0},
                connect_timeout=10,
                read_timeout=60,
            ),
        )
        parsed = urlsplit(uri)
        result = None
        try:
            if parsed.path.endswith("/"):

                def directory():
                    entries = []
                    for page in client.get_paginator("list_objects_v2").paginate(
                        Bucket=parsed.netloc, Prefix=parsed.path.lstrip("/")
                    ):
                        entries.extend(
                            {
                                "class": "File",
                                "location": f"s3://{parsed.netloc}/{item['Key']}",
                                "size": item["Size"],
                            }
                            for item in page.get("Contents", [])
                        )
                        if len(entries) > 10000:
                            raise HTTPException(413, "Directory exceeds 10000 entries")
                    return entries

                entries = await run_in_threadpool(directory)
                return JSONResponse(rewrite(entries, request, run, backend, store))
            args = {"Bucket": parsed.netloc, "Key": parsed.path.lstrip("/")}
            if request.headers.get("range"):
                args["Range"] = request.headers["range"]
            result = await run_in_threadpool(client.get_object, **args)
        except (ClientError, BotoCoreError):
            raise HTTPException(502, "Cannot retrieve backend S3 artifact") from None
        finally:
            if result is None:
                client.close()
        body = result["Body"]

        def close():
            body.close()
            client.close()

        def chunks():
            try:
                yield from body.iter_chunks(chunk_size=65536)
            finally:
                close()

        headers = {"Content-Length": str(result["ContentLength"])}
        if "ContentRange" in result:
            headers["Content-Range"] = result["ContentRange"]
        return StreamingResponse(
            chunks(),
            status_code=206 if "ContentRange" in result else 200,
            media_type=result.get("ContentType", "application/octet-stream"),
            headers=headers,
            background=BackgroundTask(close),
        )
    headers = {"Accept-Encoding": "identity"}
    if request.headers.get("range"):
        headers["Range"] = request.headers["range"]
    try:
        upstream = await backend_client.http.send(
            backend_client.http.build_request("GET", uri, headers=headers), stream=True
        )
    except httpx.TimeoutException:
        raise HTTPException(504, "Artifact backend timed out") from None
    except httpx.RequestError:
        raise HTTPException(502, "Cannot retrieve backend artifact") from None
    if upstream.is_redirect:
        await upstream.aclose()
        raise HTTPException(502, "Backend artifact redirects are not followed")
    outgoing = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower()
        in {
            "content-type",
            "content-length",
            "content-range",
            "accept-ranges",
            "content-encoding",
            "etag",
            "last-modified",
        }
    }
    return StreamingResponse(
        upstream.aiter_raw(),
        status_code=upstream.status_code,
        headers=outgoing,
        background=BackgroundTask(upstream.aclose),
    )
