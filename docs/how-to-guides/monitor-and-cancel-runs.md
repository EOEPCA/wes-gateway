# Monitor and cancel runs

Use Bash, curl and jq. Set the gateway namespace and the ID returned by a gateway
submission. For a complete runnable example, use the [curl tutorial](../tutorials/submit-and-monitor-cwl.md).

```bash
export WES_URL=http://localhost:8090/wes/v1/tenant-a
export RUN_ID=YOUR_GATEWAY_RUN_ID
mkdir -p output/monitor
```

## List runs

`GET /runs` lists records owned by this gateway database and namespace, in creation
order, oldest first. It does not return all Toil runs or filter by caller identity.
Runs submitted directly to Toil, or through a separate gateway database, are absent.
Definite rejected submissions are excluded; unresolved submissions have `UNKNOWN`
state. The gateway refreshes each known upstream run's state while producing a page.

```bash
curl --fail-with-body -sS --max-time 60 --get "$WES_URL/runs" \
  --data-urlencode 'page_size=25' \
  --output output/monitor/list.json
jq . output/monitor/list.json

NEXT_PAGE_TOKEN=$(jq -r '.next_page_token // empty' output/monitor/list.json)
if [[ -n "$NEXT_PAGE_TOKEN" ]]; then
  curl --fail-with-body -sS --max-time 60 --get "$WES_URL/runs" \
    --data-urlencode 'page_size=25' \
    --data-urlencode "page_token=$NEXT_PAGE_TOKEN" | jq .
fi
```

`page_size` defaults to 100 and accepts 1–1000. Tokens continue after the last
record on the previous page and are specific to the namespace. Pagination is not
a frozen snapshot: states can change, and newly submitted runs can appear on later
pages. An empty token marks the end of the current results; start a fresh listing
to see runs added afterward. A backend failure while refreshing states can fail
the whole page. This does not mean the gateway database has lost those runs.

## Check status and retrieve details

```bash
curl --fail-with-body -sS --max-time 60 "$WES_URL/runs/$RUN_ID/status" | jq .

curl --fail-with-body -sS --max-time 60 "$WES_URL/runs/$RUN_ID" \
  --output output/monitor/run.json
jq '{run_id, state, tags: .request.tags, outputs, run_log, task_logs}' \
  output/monitor/run.json
```

Status returns the gateway run ID and backend state. Detail includes available
outputs, workflow logs and task logs. The namespace is recorded in
`request.tags["gateway.namespace"]`; it is not an arbitrary client-controlled tag.

To retrieve a log, use its returned URL:

```bash
STDERR_URL=$(jq -r '.run_log.stderr // empty' output/monitor/run.json)
if [[ -n "$STDERR_URL" ]]; then
  curl --fail-with-body -sS --max-time 60 "$STDERR_URL" \
    --output output/monitor/stderr.txt
fi
```

Supported log/output locations become gateway artifact URLs. Other locations remain
metadata only; see [artifact configuration](configure-backends.md#enable-retrieval-of-s3-outputs).

## Task logs depend on the backend

Start with inline `task_logs` from the run detail. When the backend supports
paginated task endpoints, these requests forward to it:

```bash
curl --fail-with-body -sS --max-time 60 --get "$WES_URL/runs/$RUN_ID/tasks" \
  --data-urlencode 'page_size=100' | jq .

# Set TASK_ID to an ID returned by the backend's task listing.
TASK_ID=YOUR_TASK_ID
TASK_PATH=$(jq -rn --arg id "$TASK_ID" '$id | @uri')
curl --fail-with-body -sS --max-time 60 \
  "$WES_URL/runs/$RUN_ID/tasks/$TASK_PATH" | jq .
```

Unlike the gateway run listing, task pagination is backend-owned. Registering these
routes does not guarantee a backend implements them. An unsupported endpoint can
return an upstream error such as `404`; the gateway does not synthesize task data.

## Cancel a run

```bash
curl --fail-with-body -sS --max-time 60 \
  --request POST "$WES_URL/runs/$RUN_ID/cancel" | jq .

curl --fail-with-body -sS --max-time 60 "$WES_URL/runs/$RUN_ID/status" | jq .
```

Continue polling until `CANCELED` or another terminal state. A successful POST
acknowledges the request; `CANCELING` is still in progress. If the run remains in
that state, inspect the backend and worker logs using the
[troubleshooting guide](troubleshoot.md#cancellation-stays-in-canceling).

An unresolved submission returns `409` for cancellation and task access until
[operator reconciliation](configure-backends.md#reconcile-an-uncertain-submission).
