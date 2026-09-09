# Run your first workflow with curl

The WES Gateway is an HTTP API. In this tutorial you will submit a CWL workflow,
monitor it, and retrieve its output and logs.
All requests go to the gateway; Toil executes the workflows behind it.

## 1. Prepare your terminal

Start with a gateway [deployed with Toil WES](../how-to-guides/deploy-with-toil.md)
and a port-forward running at `http://localhost:8090`. You need Bash, `curl` with
`--fail-with-body` support, and `jq`. Open a terminal in the gateway distribution's
root directory so the supplied `examples/cwl/` files are available.

Run the commands in the same Bash session. If your gateway has a different URL
or registered namespace, substitute those values below.

```bash
set -euo pipefail

export GATEWAY_URL=http://localhost:8090
export NAMESPACE=tenant-a
export WES_URL="$GATEWAY_URL/wes/v1/$NAMESPACE"
mkdir -p output/curl-tutorial
```

The deployment guide registers `tenant-a`. The namespace in the URL selects the backend. Use `/wes/v1/tenant-a`, including the namespace,
for gateway calls. Toil's internal `/ga4gh/wes/v1` address is not needed here.

The examples use the port-forwarded gateway endpoint. If an external access layer
protects your deployment, add its required authorization headers. The gateway
itself does not authenticate callers.

## 2. Check readiness and backend capabilities

```bash
curl --fail-with-body -sS --max-time 60 "$GATEWAY_URL/readyz" | jq .

curl --fail-with-body -sS --max-time 60 "$WES_URL/service-info" |
  jq '{supported_wes_versions, workflow_type_versions, workflow_engine_versions}'
```

Readiness returns `{"status":"ready"}`. Service information comes from the
selected Toil backend. Check that it supports CWL `v1.2` before continuing. A successful service-info request confirms gateway-to-backend HTTP
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
response for `gateway_run_id` and follow [submission recovery](../how-to-guides/configure-backends.md#reconcile-an-uncertain-submission)
before submitting again.

## 4. Monitor execution

Read the current state once:

```bash
curl --fail-with-body -sS --max-time 60 "$RUN_URL/status" | jq .
```

Typical states are `QUEUED`, `RUNNING`, then `COMPLETE`. Use this function to
wait for completion:

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
the [configured artifact storage](../how-to-guides/configure-backends.md#enable-retrieval-of-s3-outputs).
The gateway can return inline `task_logs`; separate `/tasks` endpoints depend on
backend support and are not required for this tutorial.

## What you have learned

You submitted a CWL file and inputs, saved the gateway run ID, waited for completion,
and retrieved the greeting and available logs through the gateway.

To submit your own workflow or the supplied scatter example, continue with
[Submit workflow runs](../how-to-guides/submit-workflow-runs.md). To list runs or
stop execution, see [Monitor and cancel runs](../how-to-guides/monitor-and-cancel-runs.md).
