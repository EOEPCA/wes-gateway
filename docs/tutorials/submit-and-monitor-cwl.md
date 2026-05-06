# Submit and Monitor a CWL Workflow

This tutorial walks through one complete WES interaction: submit a small CWL workflow, capture the returned `run_id`, poll its status, and inspect its logs.

The gateway implements the WES API contract. The execution layer is Toil, so the workflow body and engine parameters are the same kind of values you would send to a Toil WES runner.

## Before You Start

You need a running WES endpoint. For a local Toil WES service, the base URL is normally:

```sh
export WES_URL=http://localhost:8080/ga4gh/wes/v1
```

If your deployment protects WES endpoints, also set credentials or a bearer token. The examples below use basic authentication because that is common in local Toil WES examples:

```sh
export WES_AUTH=test:test
```

## Create a Tiny CWL Workflow

Create `example.cwl`:

```yaml
cwlVersion: v1.0
class: CommandLineTool
baseCommand: echo
stdout: output.txt
inputs:
  message:
    type: string
    inputBinding:
      position: 1
outputs:
  output:
    type: stdout
```

This workflow writes the provided `message` input to `output.txt`.

## Submit the Run

Submit the workflow to `POST /runs` as multipart form data:

```sh
curl --location --request POST "$WES_URL/runs" \
  --user "$WES_AUTH" \
  --form 'workflow_url=example.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={"message":"Hello from WES"}' \
  --form 'workflow_attachment=@example.cwl'
```

A successful response returns a WES run identifier:

```json
{
  "run_id": "4deb8beb24894e9eb7c74b0f010305d1"
}
```

Keep that value. Every follow-up call uses it as `{run_id}`.

You can capture it in a shell variable if `jq` is available:

```sh
RUN_ID=$(
  curl --silent --location --request POST "$WES_URL/runs" \
    --user "$WES_AUTH" \
    --form 'workflow_url=example.cwl' \
    --form 'workflow_type=CWL' \
    --form 'workflow_type_version=v1.0' \
    --form 'workflow_params={"message":"Hello from WES"}' \
    --form 'workflow_attachment=@example.cwl' \
  | jq -r '.run_id'
)
```

## Check the Run State

Use the fast status endpoint while the workflow is running:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs/$RUN_ID/status"
```

Example response:

```json
{
  "run_id": "4deb8beb24894e9eb7c74b0f010305d1",
  "state": "RUNNING"
}
```

Terminal states include `COMPLETE`, `EXECUTOR_ERROR`, `SYSTEM_ERROR`, `CANCELED`, and `PREEMPTED`.

## Inspect the Run Log

Use `GET /runs/{run_id}` for the full run record:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs/$RUN_ID"
```

The response includes the original request, the current state, workflow logs, output locations when available, and a `task_logs_url` if the deployment supports paginated task logs.

## List Task Logs

If the deployment exposes task-level logs, list them with:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs/$RUN_ID/tasks?page_size=50"
```

Use the returned `next_page_token` to request the next page.

## Cancel If Needed

If the run is still active and should be stopped:

```sh
curl --location --request POST "$WES_URL/runs/$RUN_ID/cancel" \
  --user "$WES_AUTH"
```

The response echoes the `run_id`. Poll `GET /runs/{run_id}/status` until the state becomes `CANCELING`, `CANCELED`, or another terminal state.
