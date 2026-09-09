#!/usr/bin/env python3
"""Submit, verify, and retain gateway workflow evidence. Never retry submission."""

import argparse
import json
import time
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx


def execute(
    base_url,
    workflow,
    inputs,
    evidence,
    *,
    version="v1.2",
    entrypoint=None,
    expected=None,
    cancel=False,
    timeout=1800,
    interval=2,
):
    base_url = base_url.rstrip("/")
    workflow, evidence = Path(workflow), Path(evidence)
    evidence.mkdir(parents=True, exist_ok=True)

    def save(name, data):
        (evidence / name).write_text(json.dumps(data, indent=2) + "\n")

    with httpx.Client(timeout=60, follow_redirects=False, trust_env=False) as client:

        def request(method, url, **kwargs):
            response = client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        info = request("GET", base_url + "/service-info")
        save("service-info.json", info)
        with workflow.open("rb") as attachment:
            submission = request(
                "POST",
                base_url + "/runs",
                data={
                    "workflow_type": "CWL",
                    "workflow_type_version": version,
                    "workflow_url": workflow.name
                    + ("#" + entrypoint if entrypoint else ""),
                    "workflow_params": json.dumps(inputs),
                },
                files=[
                    ("workflow_attachment", (workflow.name, attachment, "text/plain"))
                ],
            )
        save("submission.json", submission)
        run_id = submission["run_id"]
        run_url = base_url + "/runs/" + quote(run_id, safe="")
        print(f"Run {run_id}: {run_url}", flush=True)
        states = []
        started = time.monotonic()
        cancelled = False
        while True:
            status = request("GET", run_url + "/status")
            states.append(status)
            save("statuses.json", states)
            state = status["state"]
            if len(states) == 1 or state != states[-2]["state"]:
                print(f"State: {state}", flush=True)
            if cancel and not cancelled and state == "RUNNING":
                save("cancel.json", request("POST", run_url + "/cancel"))
                cancelled = True
            if state in {"COMPLETE", "CANCELED", "EXECUTOR_ERROR", "SYSTEM_ERROR"}:
                break
            if time.monotonic() - started >= timeout:
                save("timeout-detail.json", request("GET", run_url))
                raise TimeoutError(
                    f"Monitoring timed out; run {run_id} has NOT been automatically cancelled"
                )
            time.sleep(interval)
        detail = request("GET", run_url)
        save("detail.json", detail)
        listing = request("GET", base_url + "/runs")
        while run_id not in {
            item["run_id"] for item in listing["workflows"]
        } and listing.get("next_page_token"):
            listing = request(
                "GET",
                base_url + "/runs",
                params={"page_token": listing["next_page_token"]},
            )
        assert run_id in {item["run_id"] for item in listing["workflows"]}, (
            "Run absent from namespace list"
        )
        save("listing.json", listing)
        assert state == ("CANCELED" if cancel else "COMPLETE"), (
            f"Unexpected terminal state {state}; see {evidence}"
        )
        assert (
            detail["request"]["tags"]["gateway.namespace"]
            == base_url.rsplit("/", 1)[-1]
        )
        if expected is not None:
            for key, value in expected.items():
                assert detail["outputs"][key] == value, f"Unexpected output {key}"
        retrieved = []
        for index, log in enumerate(
            [detail.get("run_log") or {}, *detail.get("task_logs", [])]
        ):
            for field in ("stdout", "stderr"):
                url = log.get(field)
                if not url:
                    continue
                assert url.startswith(run_url + "/artifacts/"), (
                    f"Log URL bypasses gateway: {field}"
                )
                response = client.get(url)
                response.raise_for_status()
                target = f"log-{index}-{field}.txt"
                (evidence / target).write_bytes(response.content)
                retrieved.append(target)

        def output_files(value):
            if isinstance(value, dict):
                location = value.get("location")
                if location:
                    yield location
                for item in value.values():
                    yield from output_files(item)
            elif isinstance(value, list):
                for item in value:
                    yield from output_files(item)
            elif isinstance(value, str) and value.startswith(run_url + "/artifacts/"):
                yield value

        for index, url in enumerate(
            dict.fromkeys(output_files(detail.get("outputs", {})))
        ):
            assert url.startswith(run_url + "/artifacts/"), (
                "Output file location bypasses gateway"
            )
            response = client.get(url)
            response.raise_for_status()
            target = f"output-{index}.bin"
            (evidence / target).write_bytes(response.content)
            retrieved.append(target)
        save(
            "result.json",
            {
                "run_id": run_id,
                "namespace": base_url.rsplit("/", 1)[-1],
                "state": state,
                "outputs": detail.get("outputs"),
                "retrieved": retrieved,
                "elapsed_seconds": round(time.monotonic() - started, 2),
            },
        )
        print(f"Verified {run_id}; evidence: {evidence}", flush=True)
        return run_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "base_url", help="Gateway WES URL including /wes/v1/{namespace}"
    )
    parser.add_argument("workflow", type=Path)
    parser.add_argument("inputs", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--expected", type=Path, help="Expected output key/value JSON")
    parser.add_argument("--version", default="v1.2")
    parser.add_argument("--entrypoint")
    parser.add_argument("--cancel", action="store_true")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if urlsplit(args.base_url).scheme not in {"http", "https"}:
        parser.error("base_url must be HTTP(S)")
    execute(
        args.base_url,
        args.workflow,
        json.loads(args.inputs.read_text()),
        args.evidence,
        version=args.version,
        entrypoint=args.entrypoint,
        expected=json.loads(args.expected.read_text()) if args.expected else None,
        cancel=args.cancel,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
