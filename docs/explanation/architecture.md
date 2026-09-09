# Architecture

Clients call `/wes/v1/{namespace}` on the gateway. A validated declarative registry
maps the logical namespace to a backend WES HTTP API. Toil handles execution,
Celery, Kubernetes jobs, and workflow storage in its own deployment.

![Helm deployment and backend connections](../diagrams/out/overall.svg)

The gateway stores a durable record before submission, forwards multipart workflow
fields and attachments, and returns a gateway run ID. Subsequent status, detail,
cancellation, task and artifact requests resolve that ID within its namespace and
use the original backend. Reserved request tags carry the namespace association
and support recovery after an ambiguous submission. Database-backed pagination
exposes only gateway-owned runs, even when multiple namespaces share a backend.

![Submission, namespace ownership and listing sequence](../diagrams/out/sequence.svg)

The gateway preserves backend WES JSON and meaningful error statuses. In particular,
Toil 9.4.1 reports WES 1.0 service metadata, which is not forced through the generated
1.1 response models. `/service-info` reports the backend's actual capabilities, with
potentially sensitive `--setEnv` defaults removed. Task endpoints forward backend
support or errors; the gateway does not invent task data for unsupported routes.

Run records use SQLite in the single-replica development deployment and can use
PostgreSQL for shared metadata across replicas. Stable backend identities cannot
be silently repointed while recorded runs exist. The gateway never retries run
submission or cancellation automatically.

HTTP logs from the backend are exposed through stored, opaque, run-scoped artifact
links. Explicitly configured S3 outputs can be streamed through the same routes.
This preserves access through the gateway without accepting arbitrary fetch URLs.

Implementation modules are `config.py` (registry validation), `backend.py` (HTTP
transport), `store.py` (durable metadata), `main.py` (routing), `artifacts.py`
(retrieval), and `reconcile.py` (operator recovery). `models.py` remains the upstream
schema model reference. Skeleton generation writes to `generated/`, so it cannot
overwrite handwritten gateway implementation.

See [configuration and operation](../how-to-guides/configure-backends.md) for
configuration, persistence, recovery, and deployment limits. Identity-based
OIDC/JWT authorization is not yet implemented in this application.
