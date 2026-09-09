"""HTTP transport shared by all WES adapters. Mutating requests are never retried."""

import os

import httpx
from fastapi import HTTPException


class BackendClient:
    def __init__(self, config, transport=None):
        self.config = config
        headers = {}
        if config.bearer_token_env:
            headers["Authorization"] = "Bearer " + os.environ[config.bearer_token_env]
        self.http = httpx.AsyncClient(
            timeout=httpx.Timeout(config.read_timeout, connect=config.connect_timeout),
            verify=config.verify_tls,
            limits=httpx.Limits(keepalive_expiry=config.keepalive_expiry),
            headers=headers,
            transport=transport,
            follow_redirects=False,
            trust_env=False,
        )

    async def request(self, method, path, **kwargs):
        try:
            response = await self.http.request(
                method, self.config.base_url + path, **kwargs
            )
        except httpx.TimeoutException:
            raise HTTPException(504, "WES backend timed out") from None
        except httpx.RequestError as exc:
            # Expose the exception type, never its potentially credential-bearing URL.
            raise HTTPException(
                502, f"WES backend transport failed ({type(exc).__name__})"
            ) from None
        return response

    async def json(self, method, path, **kwargs):
        response = await self.request(method, path, **kwargs)
        try:
            payload = response.json()
        except ValueError:
            if response.is_error:
                payload = {
                    "msg": "WES backend request failed",
                    "status_code": response.status_code,
                }
            else:
                raise HTTPException(502, "WES backend returned invalid JSON") from None
        if not isinstance(payload, dict):
            raise HTTPException(502, "WES backend returned an invalid response")
        return response, payload

    async def close(self):
        await self.http.aclose()
