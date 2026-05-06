# Monitor and Cancel Runs

After `POST /runs` returns a `run_id`, use the run endpoints to track state, collect logs, inspect task details, and stop active work.

## List Runs

Use `GET /runs` to retrieve runs visible to the caller:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs?page_size=25"
```

If the response includes `next_page_token`, request the next page:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs?page_size=25&page_token=$NEXT_PAGE_TOKEN"
```

The ordering is stable for the paging session, but clients should not assume that new live updates appear during the same paging pass.

## Check Fast Status

Use `GET /runs/{run_id}/status` for a lightweight status response:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs/$RUN_ID/status"
```

Example:

```json
{
  "run_id": "4deb8beb24894e9eb7c74b0f010305d1",
  "state": "COMPLETE"
}
```

Use this endpoint for polling dashboards and automation.

## Get Full Run Details

Use `GET /runs/{run_id}` when you need the submitted request, output object, run log, or task log URL:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs/$RUN_ID"
```

The `run_log` object can include command, start time, end time, stdout URL, stderr URL, exit code, and system logs. The `outputs` object contains workflow outputs when they are available.

## List Task Logs

Use `GET /runs/{run_id}/tasks` for paginated task logs:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs/$RUN_ID/tasks?page_size=100"
```

Each `TaskLog` includes a task `id`, task name, command, timing, stdout and stderr URLs, exit code, and optional system logs.

## Get One Task

Use `GET /runs/{run_id}/tasks/{task_id}` for a single task:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs/$RUN_ID/tasks/$TASK_ID"
```

This is useful when a workflow has many tasks and the client already knows which task failed.

## Cancel a Run

Use `POST /runs/{run_id}/cancel`:

```sh
curl --location --request POST "$WES_URL/runs/$RUN_ID/cancel" \
  --user "$WES_AUTH"
```

Then poll status:

```sh
curl --user "$WES_AUTH" "$WES_URL/runs/$RUN_ID/status"
```

Cancellation is asynchronous. Depending on timing, a run may move through `CANCELING` before `CANCELED`, or it may already be in another terminal state.
