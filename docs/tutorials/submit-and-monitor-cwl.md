# Run a workflow through the gateway with curl

The WES Gateway is an HTTP API. In this tutorial you will submit a CWL workflow,
monitor it, retrieve its output and logs, and cancel a separate running workflow.
All requests go to the gateway; Toil executes the workflows behind it.

## 1. Prepare your terminal

Keep `skaffold dev --port-forward` running in one terminal. Open another Bash
terminal in the **wes-gateway repository root**. You need `curl` with
`--fail-with-body` support and `jq` for reading JSON responses.

Run all the following commands in that same Bash session. If you are using the
optional local Python gateway on port 8091, change `GATEWAY_URL` accordingly:

```bash
set -euo pipefail

export GATEWAY_URL=http://localhost:8090
export NAMESPACE=tenant-a
export WES_URL="$GATEWAY_URL/wes/v1/$NAMESPACE"
mkdir -p output/curl-tutorial
```

`tenant-a` and `tenant-b` are registered in `config/backends.yaml`. The namespace
in the URL selects the backend. Use `/wes/v1/tenant-a`, including the namespace,
for gateway calls. Toil's internal `/ga4gh/wes/v1` address is not needed here.

The examples use the local development endpoint. If an external access layer
protects your deployment, add its required authorization headers. The gateway
itself does not authenticate callers.

## 2. Check readiness and backend capabilities

```bash
curl --fail-with-body -sS --max-time 60 "$GATEWAY_URL/readyz" | jq .

curl --fail-with-body -sS --max-time 60 "$WES_URL/service-info" |
  jq '{supported_wes_versions, workflow_type_versions, workflow_engine_versions}'
```

Readiness returns `{"status":"ready"}`. Service information comes from the
selected Toil backend: the evaluated deployment reports WES `1.0.0` and supports
CWL `v1.2`. A successful service-info request confirms gateway-to-backend HTTP
connectivity; the workflow submission below checks execution.

Swagger UI is available at [http://localhost:8090/docs](http://localhost:8090/docs).

## 3. Submit Hello World once

Use the bundled `examples/cwl/hello.cwl`. It runs a containerized `echo` command
and returns its greeting as a string. `hello.inputs.json` supplies the message.

```bash
curl --fail-with-body -sS --max-time 60 \
  --request POST "$WES_URL/runs" \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.2' \
  --form 'workflow_url=hello.cwl' \
  --form 'workflow_attachment=@examples/cwl/hello.cwl' \
  --form 'workflow_params=<examples/cwl/hello.inputs.json' \
  --form 'tags={"tutorial":"curl-hello"}' \
  --output output/curl-tutorial/submission.json

cat output/curl-tutorial/submission.json | jq .
RUN_ID=$(jq -er '.run_id | select(type == "string" and length > 0)' \
  output/curl-tutorial/submission.json)
RUN_URL="$WES_URL/runs/$RUN_ID"
printf 'Gateway run ID: %s\n' "$RUN_ID"
```

The response has this shape, with a different ID for each submission:

```json
{"run_id":"4deb8beb24894e9eb7c74b0f010305d1"}
```

`workflow_attachment=@...` uploads the CWL file. `workflow_params=<...` reads the
JSON file into a **text form field**, which is what WES expects. `workflow_url`
identifies the uploaded filename. Let curl set the multipart Content-Type and
boundary automatically.

The returned ID is owned by the gateway and associated with this namespace.
Keep it for every subsequent call. A repeated `POST /runs` creates another run.
If submission times out or returns an unknown-outcome error, inspect the saved
response for `gateway_run_id` and follow [submission recovery](../how-to-guides/configure-backends.md#namespace-ownership-and-run-recovery)
before submitting again.

## 4. Monitor execution

Read the current state once:

```bash
curl --fail-with-body -sS --max-time 60 "$RUN_URL/status" | jq .
```

Typical states are `QUEUED`, `RUNNING`, then `COMPLETE`. Define this polling
function so you can also reuse it for the cancellation example:

```bash
wait_for_state() (
  run_url=$1
  expected=$2
  deadline=$((SECONDS + 1800))

  while (( SECONDS < deadline )); do
    response=$(curl --fail-with-body -sS --max-time 60 "$run_url/status") || exit 1
    state=$(jq -er '.state' <<< "$response") || exit 1
    printf 'State: %s\n' "$state"
    if [[ "$state" == "$expected" ]]; then
      exit 0
    fi
    case "$state" in
      COMPLETE|CANCELED|EXECUTOR_ERROR|SYSTEM_ERROR|PREEMPTED)
        printf 'Reached %s while waiting for %s. Inspect %s\n' \
          "$state" "$expected" "$run_url" >&2
        exit 1
        ;;
    esac
    sleep 2
  done

  printf 'Monitoring timed out; no cancellation was sent. Inspect %s\n' \
    "$run_url" >&2
  exit 1
)

wait_for_state "$RUN_URL" COMPLETE
```

The function stops on a terminal failure or after 30 minutes. Stopping monitoring
or closing the terminal does not cancel execution. To inspect a failure, retrieve
run details and logs using the next step.

## 5. Retrieve the output and logs

```bash
curl --fail-with-body -sS --max-time 60 "$RUN_URL" \
  --output output/curl-tutorial/run.json

jq '{run_id, state, tags: .request.tags, outputs, run_log}' \
  output/curl-tutorial/run.json

jq -e '.outputs.greeting == "Hello through the WES Gateway!\n"' \
  output/curl-tutorial/run.json
```

The last command prints `true` and succeeds when the greeting matches. The output
is a string in this example; no separate output-file download is required.
`request.tags` includes `gateway.namespace`, `gateway.backend`, and
`gateway.run_id`, together with your tutorial tag.

Download any available workflow stdout and stderr through the returned gateway
artifact URLs:

```bash
for stream in stdout stderr; do
  log_url=$(jq -r --arg stream "$stream" '.run_log[$stream] // empty' \
    output/curl-tutorial/run.json)
  if [[ -n "$log_url" ]]; then
    curl --fail-with-body -sS --max-time 60 "$log_url" \
      --output "output/curl-tutorial/$stream.txt"
    printf 'Saved %s\n' "output/curl-tutorial/$stream.txt"
  fi
done
```

Use the URLs returned by the API; do not construct Toil log URLs yourself. Other
workflows may produce File or Directory outputs. Their byte retrieval depends on
the [configured artifact storage](../how-to-guides/configure-backends.md#logs-and-output-files).
The gateway can return inline `task_logs`; separate `/tasks` endpoints depend on
backend support and are not required for this tutorial.

## 6. List runs and check namespace isolation

```bash
curl --fail-with-body -sS --max-time 60 --get "$WES_URL/runs" \
  --data-urlencode 'page_size=2' \
  --output output/curl-tutorial/list.json
jq . output/curl-tutorial/list.json

NEXT_PAGE_TOKEN=$(jq -r '.next_page_token // empty' output/curl-tutorial/list.json)
if [[ -n "$NEXT_PAGE_TOKEN" ]]; then
  curl --fail-with-body -sS --max-time 60 --get "$WES_URL/runs" \
    --data-urlencode 'page_size=2' \
    --data-urlencode "page_token=$NEXT_PAGE_TOKEN" | jq .
fi
```

Results use the `workflows` key, not `runs`. Each entry has `run_id`, `state`, and
`tags`; full outputs and logs require `GET /runs/{run_id}`. Only records in this
gateway database and namespace are listed, oldest first. Therefore, `page_size=2`
returns the first two records, which may not include the run you just submitted.
Use the saved `$RUN_URL` to retrieve that run directly, or follow pagination.

Runs submitted directly to Toil or through the earlier local gateway database
will not appear in the Helm deployment's listing. An empty result is valid:
`{"workflows":[],"next_page_token":""}`. States are refreshed on each request,
and new submissions can appear on later pages; pagination is not a snapshot.
Pagination tokens belong to the namespace that issued them; encode them with `--data-urlencode` when sending them back.

The following requests intentionally return **404**. They omit `--fail-with-body`
so you can inspect those expected errors without stopping the Bash session:

```bash
OTHER_NAMESPACE=tenant-b
if [[ "$NAMESPACE" == tenant-b ]]; then OTHER_NAMESPACE=tenant-a; fi

curl -sS --max-time 60 --write-out '\nHTTP %{http_code}\n' \
  "$GATEWAY_URL/wes/v1/$OTHER_NAMESPACE/runs/$RUN_ID/status"

curl -sS --max-time 60 --write-out '\nHTTP %{http_code}\n' \
  "$GATEWAY_URL/wes/v1/not-registered/runs"
```

To execute in tenant B, set `NAMESPACE=tenant-b`, rebuild `WES_URL`, and submit a
new run. An existing run ID remains associated with its original namespace.

## 7. Cancel a running workflow

Hello World finishes quickly, so submit the separate sleep workflow for this
exercise. It normally sleeps for five minutes. Wait until it is `RUNNING` before
sending the cancellation request; immediate queued cancellation in the evaluated
Toil deployment can remain at `CANCELING`.

```bash
curl --fail-with-body -sS --max-time 60 \
  --request POST "$WES_URL/runs" \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.2' \
  --form 'workflow_url=cancel.cwl' \
  --form 'workflow_attachment=@examples/cwl/cancel.cwl' \
  --form 'workflow_params=<examples/cwl/cancel.inputs.json' \
  --output output/curl-tutorial/cancel-submission.json

CANCEL_RUN_ID=$(jq -er '.run_id | select(type == "string" and length > 0)' \
  output/curl-tutorial/cancel-submission.json)
CANCEL_RUN_URL="$WES_URL/runs/$CANCEL_RUN_ID"

wait_for_state "$CANCEL_RUN_URL" RUNNING

curl --fail-with-body -sS --max-time 60 \
  --request POST "$CANCEL_RUN_URL/cancel" | jq .

wait_for_state "$CANCEL_RUN_URL" CANCELED

curl --fail-with-body -sS --max-time 60 "$CANCEL_RUN_URL" \
  --output output/curl-tutorial/cancel-run.json
```

A successful cancellation POST means the request was accepted. Confirming
`CANCELED` via the status endpoint verifies that cancellation completed.
`CANCELING` is an intermediate state.

## 8. Try the existing scatter workflow

Submit `scatter.cwl` using the same multipart fields:

```bash
curl --fail-with-body -sS --max-time 60 \
  --request POST "$WES_URL/runs" \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.2' \
  --form 'workflow_url=scatter.cwl' \
  --form 'workflow_attachment=@examples/cwl/scatter.cwl' \
  --form 'workflow_params=<examples/cwl/scatter.inputs.json' \
  --output output/curl-tutorial/scatter-submission.json

SCATTER_RUN_ID=$(jq -er '.run_id | select(type == "string" and length > 0)' \
  output/curl-tutorial/scatter-submission.json)
SCATTER_RUN_URL="$WES_URL/runs/$SCATTER_RUN_ID"
wait_for_state "$SCATTER_RUN_URL" COMPLETE

curl --fail-with-body -sS --max-time 60 "$SCATTER_RUN_URL" \
  --output output/curl-tutorial/scatter-run.json

jq -e --slurpfile expected examples/cwl/scatter.expected.json \
  '.outputs == $expected[0]' output/curl-tutorial/scatter-run.json
```

This checks the three greeting strings, their ordering, and their trailing
newlines. The water-bodies workflow is deferred until its evaluated package and
inputs are supplied.
