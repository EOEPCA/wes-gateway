# API reference

The public base path is `/wes/v1/{namespace}`. `/openapi.json` and `/docs` on the
running gateway describe its routes. The checked-in upstream OpenAPI document and
its HTML rendering are a WES schema reference, not the gateway routing contract.

| Method | Resource | Behavior |
| --- | --- | --- |
| GET | `/service-info` | Backend capabilities; deployment `--setEnv` defaults omitted |
| POST | `/runs` | Submit multipart fields/attachments; return a durable gateway run ID |
| GET | `/runs` | Namespace-owned runs and refreshed states, with gateway pagination |
| GET | `/runs/{run_id}` | Request, state, logs, outputs, and reserved namespace tags |
| GET | `/runs/{run_id}/status` | Gateway run ID and current backend state |
| POST | `/runs/{run_id}/cancel` | Forward cancellation; poll status for terminal state |
| GET | `/runs/{run_id}/tasks` | Forward task listing if the backend supports it |
| GET | `/runs/{run_id}/tasks/{task_id}` | Forward task detail if supported |
| GET | `/runs/{run_id}/artifacts/{token}` | Stream a recorded run-scoped log/output artifact |

Multipart submission requires `workflow_url`, `workflow_type`,
`workflow_type_version`, and JSON-object `workflow_params`. Optional fields are
JSON-object `tags` and `workflow_engine_parameters`, `workflow_engine`,
`workflow_engine_version`, and repeated `workflow_attachment` files. A workflow
engine version requires a workflow engine. URL-only submissions need no attachment.
Duplicate scalar fields, unknown fields, invalid JSON, missing required fields,
or unsafe/duplicate attachment filenames return `400`. Tags and engine parameters
map strings to strings. The multipart parser allows at most 100 files and 100
text fields, with the total body bounded by `max_upload_bytes`. Accepted filenames
and packed-workflow fragments are forwarded unchanged.

Lists return `workflows` and `next_page_token`. They accept `page_size` (1–1000,
default 100) and an opaque namespace-scoped `page_token`. Records are oldest first
in gateway creation order; the first page is not a list of the newest runs. States
are refreshed per request and new records can appear on later pages. There is no
snapshot, tag filter, or caller-identity filter. Direct-Toil runs and runs stored
in a different gateway database are excluded. An empty namespace returns
`{"workflows":[],"next_page_token":""}`. Detail request tags and list summary
tags include `gateway.namespace`, `gateway.backend`, and `gateway.run_id`.

Backend JSON is preserved rather than validated as a newer WES version. Toil 9.4.1
advertises WES 1.0; task routes may be unavailable. The OpenAPI info version is
`1.1.0`; it does not claim that every registered backend supports WES 1.1. The
gateway preserves actual states and never turns `CANCELING` into `CANCELED` without backend confirmation.
An ambiguous submission has `UNKNOWN` state until operator reconciliation.

| Status | Meaning |
| --- | --- |
| 400 | Invalid request fields, namespace-scoped page token, or upstream client error |
| 404 | Unknown namespace, run not owned by namespace, missing artifact/task |
| 409 | Submission must be reconciled before cancellation/task retrieval |
| 413 | Configured upload or directory listing limit exceeded |
| 502 | Backend transport, JSON, or artifact retrieval failure |
| 503 | Run metadata storage unavailable |
| 504 | Backend timeout |

Gateway errors contain `msg` and `status_code`. Upstream error status and JSON are
preserved where available. Unknown submission outcomes also include
`gateway_run_id`; do not automatically retry submission. No client identity is
validated by these routes; external authentication/authorization is required.

Unprefixed `/runs` and `/service-info`, and `/ga4gh/wes/v1/...`, return `404` unless
`default_namespace` is configured. With a default they return `307` redirects to
namespaced routes, preserving method and query. Configure clients with the final
namespaced URL to avoid submission redirects.
