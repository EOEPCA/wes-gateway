"""Recover ambiguous submissions using gateway-owned tags. Never resubmit work."""

import asyncio
import os
from urllib.parse import quote

from .backend import BackendClient
from .config import load_registry
from .store import RunStore


async def reconcile():
    registry = load_registry(
        os.environ.get("WES_BACKENDS_CONFIG", "config/backends.yaml")
    )
    store = RunStore(os.environ.get("WES_DATABASE_URL", "sqlite:///./wes-gateway.db"))
    try:
        store.validate_bindings(registry)
        for run in store.unresolved():
            client = BackendClient(registry.backends[run["backend"]])
            matches = []
            try:
                token, seen = "", set()
                while True:
                    response, listing = await client.json(
                        "GET", "/runs", params={"page_size": 100, "page_token": token}
                    )
                    response.raise_for_status()
                    for item in listing.get("workflows", []):
                        upstream_id = item["run_id"]
                        response, detail = await client.json(
                            "GET", "/runs/" + quote(upstream_id, safe="")
                        )
                        response.raise_for_status()
                        tags = (detail.get("request") or {}).get("tags") or {}
                        if (
                            tags.get("gateway.run_id") == run["id"]
                            and tags.get("gateway.namespace") == run["namespace"]
                        ):
                            matches.append(upstream_id)
                    token = listing.get("next_page_token")
                    if not token:
                        break
                    if token in seen:
                        raise RuntimeError("Backend repeated pagination token")
                    seen.add(token)
                if len(matches) == 1:
                    store.accepted(run["id"], matches[0])
                    print(f"{run['id']}: recovered")
                else:
                    print(
                        f"{run['id']}: unresolved ({len(matches)} matching runs); no workflow submitted"
                    )
            finally:
                await client.close()
    finally:
        store.close()


if __name__ == "__main__":
    asyncio.run(reconcile())
