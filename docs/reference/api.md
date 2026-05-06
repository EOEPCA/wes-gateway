# API Reference

The gateway exposes the GA4GH WES API through FastAPI. The generated source in `src/wes_api_gateway/main.py` declares the route functions, and `src/wes_api_gateway/models.py` declares the Pydantic response and data models.

For the full OpenAPI rendering, see the [generated OpenAPI page](../c4/components/OpenAPI/apidoc.html).

## Base URL

The OpenAPI server template uses:

```text
https://{defaultHost}/{basePath}/{apiVersion}
```

The default WES path is:

```text
/ga4gh/wes/v1
```

In examples, this documentation uses:

```sh
export WES_URL=http://localhost:8080/ga4gh/wes/v1
```

## Endpoints

| Method | Path | FastAPI function | Response model | Purpose |
| --- | --- | --- | --- | --- |
| `GET` | `/service-info` | `get_service_info` | `ServiceInfo` | Discover supported WES versions, workflow types, Toil engine versions, filesystem protocols, state counts, and service metadata. |
| `GET` | `/runs` | `list_runs` | `RunListResponse` | List runs visible to the caller. Supports `page_size` and `page_token`. |
| `POST` | `/runs` | `run_workflow` | `RunId` | Submit a workflow run as multipart form data. |
| `GET` | `/runs/{run_id}` | `get_run_log` | `RunLog` | Return detailed run request, state, logs, task log URL, and outputs. |
| `GET` | `/runs/{run_id}/status` | `get_run_status` | `RunStatus` | Return a lightweight run state response. |
| `POST` | `/runs/{run_id}/cancel` | `cancel_run` | `RunId` | Request cancellation for a run. |
| `GET` | `/runs/{run_id}/tasks` | `list_tasks` | `TaskListResponse` | List task logs for a run. Supports `page_size` and `page_token`. |
| `GET` | `/runs/{run_id}/tasks/{task_id}` | `get_task` | `TaskLog` | Return one task log. |

## Run Submission Fields

`POST /runs` uses `multipart/form-data`.

| Field | Required | Type | Description |
| --- | --- | --- | --- |
| `workflow_url` | yes | string | Primary CWL or WDL document. Can be absolute, or relative to an uploaded `workflow_attachment`. |
| `workflow_type` | yes | string | Workflow descriptor type, such as `CWL` or `WDL`, if supported by the deployment. |
| `workflow_type_version` | yes | string | Descriptor version, such as `v1.0`. Check `GET /service-info` for supported values. |
| `workflow_params` | usually | JSON object encoded as string | Workflow inputs and output locations. The shape depends on the workflow language. |
| `workflow_attachment` | no | file array | Uploaded workflow files, tools, or inputs used by the run. |
| `workflow_engine` | no | string | Workflow engine name. This gateway is intended to run through Toil. |
| `workflow_engine_version` | no | string | Requested engine version, when the deployment supports version selection. |
| `workflow_engine_parameters` | no | JSON object encoded as string | Engine parameters passed to Toil, subject to deployment policy. |
| `tags` | no | JSON object encoded as string | Client metadata stored with the run. |

## Run States

The `State` enum in `models.py` contains:

| State | Meaning |
| --- | --- |
| `UNKNOWN` | The state is not known or was not reported. |
| `QUEUED` | The run is waiting to start. |
| `INITIALIZING` | The run has been assigned and is preparing to execute. |
| `RUNNING` | The workflow is executing. |
| `PAUSED` | The workflow is paused, if supported by the implementation. |
| `COMPLETE` | The workflow finished successfully. |
| `EXECUTOR_ERROR` | A workflow executor process failed. |
| `SYSTEM_ERROR` | The service or infrastructure failed outside the workflow executor. |
| `CANCELED` | The run was cancelled. |
| `CANCELING` | Cancellation has been requested and is in progress. |
| `PREEMPTED` | The run was stopped because compute capacity was reclaimed. |

## ServiceInfo

`GET /service-info` returns `ServiceInfo`, which extends GA4GH service metadata with WES-specific capability fields:

- `workflow_type_versions`
- `supported_wes_versions`
- `supported_filesystem_protocols`
- `workflow_engine_versions`
- `default_workflow_engine_parameters`
- `system_state_counts`
- `auth_instructions_url`
- `tags`

Use this endpoint to make a client adaptive. A client should not hard-code CWL, WDL, Toil version, filesystem protocol, or authentication assumptions if the deployment reports them dynamically.

## Error Responses

The source declares `ErrorResponse` for common error statuses:

| Status | Typical meaning |
| --- | --- |
| `400` | Malformed request. |
| `401` | Authentication is missing or invalid. |
| `403` | Caller is authenticated but not authorized for the action. |
| `404` | Requested run or task does not exist or is not visible to the caller. |
| `500` | Unexpected service error. |

`ErrorResponse` contains `msg` and `status_code`.
