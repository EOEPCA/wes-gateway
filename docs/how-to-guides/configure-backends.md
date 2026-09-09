# Configure and operate WES backends

The gateway proxies WES over HTTP. Toil remains responsible for scheduling,
workflow execution, storage, and cancellation. The sample registry registers the
two Services defined by the separate `toil-bootstrap` repository.

For a first installation and failure diagnosis, see
[Deploy with Toil WES](deploy-with-toil.md). This page covers configuration options
and ongoing operation.

## Deploy with Helm through Skaffold

Run from the repository root with the Toil stack already deployed, an accessible
Docker daemon, Helm, Skaffold, and a Kubernetes context with a default StorageClass:

```sh
helm lint charts/wes-gateway --set-file backendConfig=config/backends.yaml
skaffold dev --port-forward
```

Skaffold builds the Dockerfile, passes the resulting image as `image.ref`, and
installs Helm release `wes-gateway` in namespace `wes-gateway`. It waits for
readiness, forwards port 8090, and watches files for changes. Use
`skaffold run --port-forward` for a single build/deploy without file watching.

If your account already belongs to the Docker group but your current process has
not acquired that membership, launch it from a refreshed login session, or use:

```sh
sg docker -c 'skaffold dev --port-forward'
```

The chart uses a Deployment and Service; Knative and Kustomize are not required.
SQLite metadata lives on a 1 GiB PVC, with one replica and a Recreate strategy.
Readiness checks metadata storage, while liveness is independent of Toil
availability. Gateway networking must reach each configured backend and artifact
store; the gateway does not need Kubernetes permissions to manage workflow pods.

Skaffold passes the complete `config/backends.yaml` to Helm as `backendConfig`
using `--set-file`. This replaces the chart's `registry` values in full. A checksum
annotation on the pod template changes when the effective registry changes, so a
Helm upgrade rolls the pod. There is no in-process config reload or public
backend-registration API.

For direct Helm installation of an image you have already built and made available
to the cluster:

```sh
helm upgrade --install wes-gateway charts/wes-gateway \
  --namespace wes-gateway --create-namespace \
  --set image.ref=YOUR_REGISTRY/wes-gateway:YOUR_TAG \
  --set-file backendConfig=config/backends.yaml \
  --wait
```

| Chart value | Default | Purpose |
| --- | --- | --- |
| `image.ref` | Empty; repository/tag fallback | Fully qualified image supplied by Skaffold |
| `service.port` | 8090 | Kubernetes Service port; the container listens on 8090 |
| `replicaCount` | 1 | SQLite requires one replica |
| `persistence.enabled` | true | Mount metadata storage at `/data` |
| `persistence.size` | 1Gi | Size of a chart-created PVC |
| `persistence.storageClass` | Empty | Use the cluster default class |
| `persistence.existingClaim` | Empty | Use a PVC managed outside this release |
| `database.url` | `sqlite:////data/wes-gateway.db` | Database URL when no Secret is configured |
| `database.secretName`, `database.secretKey` | Empty | Set together to read the URL from a Secret |
| `extraEnv` | Empty list | Kubernetes environment entries, including backend credential Secret references |

Chart-created PVCs are removed on Helm uninstall, including normal `skaffold dev`
cleanup. Use `persistence.existingClaim` with an externally managed PVC when run
metadata must survive teardown. A pod restart or upgrade using the same PVC keeps
its records. Input/workflow data in Toil is separate from this gateway database.

For multiple gateway replicas, provision PostgreSQL and set the database Secret
to a `postgresql+psycopg://...` URL. The image already includes the driver; local
installations need `.[postgres]`. All replicas must use the same database and
registry. Initialize the schema with one process before starting more replicas.
You can disable the gateway PVC for PostgreSQL. Helm cannot validate a Secret's
contents: ensure it holds a PostgreSQL URL before increasing `replicaCount`.
PostgreSQL availability and future database schema migrations are operator-managed.

## Run the gateway as a local Python process

This is an alternative to the deployed gateway. Use a separate port (8091 below)
to avoid colliding with Skaffold's gateway port forward on 8090. The checked-in
registry uses Kubernetes DNS, so first forward Toil in two separate terminals:

```sh
kubectl port-forward -n tenant-a service/toil-wes 18080:8080
```

```sh
kubectl port-forward -n tenant-b service/toil-wes 18081:8080
```

In the repository root, create a separate local registry and start the process:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e . pytest
mkdir -p output/local
cat > output/local/backends.yaml <<'YAML'
version: 1
backends:
  toil-a:
    type: toil
    base_url: http://127.0.0.1:18080/ga4gh/wes/v1
  toil-b:
    type: toil
    base_url: http://127.0.0.1:18081/ga4gh/wes/v1
namespaces:
  tenant-a:
    backend: toil-a
  tenant-b:
    backend: toil-b
YAML
export WES_BACKENDS_CONFIG="$PWD/output/local/backends.yaml"
export WES_DATABASE_URL="sqlite:///$PWD/output/local/wes-gateway.db"
.venv/bin/uvicorn wes_api_gateway.main:app --port 8091
```

Use `http://localhost:8091/wes/v1/tenant-a` for this process. Its database is separate
from the deployed gateway's PVC: runs created through one will not appear in the
other. Keep backend IDs and base URLs stable for a database with recorded runs.
Restart this local process after changing its registry.

## Registry contract

To extend an existing installation, follow [Add additional backends](add-backends.md)
for registration, credentials, rollout and verification examples.

`version`, `backends`, and `namespaces` are required. Each logical namespace maps
to a registered backend ID; it need not equal a Kubernetes namespace. Both `toil`
and `wes` types use the WES HTTP transport, allowing other compatible services to
be registered without changing routes. Other adapter types are rejected.

| Setting | Default | Meaning |
| --- | --- | --- |
| Backend `base_url` | Required | Full WES API root including `/ga4gh/wes/v1`, with no query, fragment, or credentials |
| `connect_timeout` | 10 seconds | Connection timeout, positive and at most 300 seconds |
| `read_timeout` | 60 seconds | HTTP read/write/pool timeout, positive and at most 3600 seconds |
| `keepalive_expiry` | 1 second | Expire idle connections before Toil closes them; set 0 to disable reuse |
| `verify_tls` | `true` | Validate upstream TLS certificates |
| `bearer_token_env` | None | Environment variable containing a backend bearer token |
| Registry `max_upload_bytes` | 67108864 | Total incoming request size limit, including multipart framing |
| Registry `default_namespace` | None | Optional namespace for legacy route redirects |

Unknown fields, duplicate YAML keys, invalid IDs/URLs/timeouts, unsupported
versions/types, missing namespace references, and missing credential environment
variables fail startup with field-level errors. A temporarily unavailable backend
does not invalidate the registry or prevent other namespaces from operating.

Use Kubernetes Secret `secretKeyRef` entries to populate any credential environment
variables. The gateway does not forward client Authorization or arbitrary request
headers to Toil. Toil service-info's `--setEnv` defaults are omitted because Toil
can expose deployment credentials there.

## Namespace ownership and run recovery

The gateway returns its own durable run ID and records the original backend ID,
upstream run ID, namespace, and creation time. Detail responses expose reserved
`request.tags` keys `gateway.namespace`, `gateway.backend`, and `gateway.run_id`.
Client-supplied values for these keys are overwritten. List entries include those
tags. Run IDs from direct-Toil submissions are not imported or exposed.

Listings are paginated from gateway-owned records and refresh each returned run's
state using its original backend. This avoids mixing runs when logical namespaces
share a backend. `page_size` is 1–1000 (default 100); opaque `page_token` values are
namespace-scoped. Results are oldest first, following gateway record creation
order, and are not a snapshot: states can change and new runs may appear on later
pages. Backend list tokens are not exposed as gateway tokens. A failure
refreshing a page is returned to the caller; other namespaces remain usable.

A namespace can be remapped for future submissions; existing runs stay associated
with their original backend. A backend ID with recorded runs cannot be removed or
assigned a different type/base URL: startup fails and instructs the operator to
add a new ID. Keep old registrations and logical namespaces available while their
runs must remain accessible. Back up the metadata database with workflow data.

Submission creates a durable record before contacting Toil, and injects the gateway
ID into request tags. A timeout or recording failure can leave an unknown outcome.
The error includes `gateway_run_id`; its status is `UNKNOWN`, and cancellation
returns `409` until reconciled. **Do not blindly resubmit:** Toil may have accepted
the workflow. Reconcile against the same registry and database after stopping
the relevant submission activity.

For the local Python process, keep its registry/database environment variables set:

```sh
.venv/bin/python -m wes_api_gateway.reconcile
```

For the default Helm deployment, run inside the gateway container to use its mounted
registry, database and credentials:

```sh
kubectl exec -n wes-gateway deployment/wes-gateway -- \
  python -m wes_api_gateway.reconcile
```

It scans upstream runs, matches both reserved run ID and namespace tags, and binds
a record only when exactly one match exists. It never submits or cancels work.
Zero/multiple matches remain unresolved for operator investigation. Backend tag
persistence is required for automatic recovery. Definite upstream 4xx rejections
are excluded from listings; ambiguous failures remain visible.

## Logs and output files

Run detail JSON includes scalar outputs and logs. For backend HTTP(S) log/output
references on the configured backend origin whose path contains the upstream run
ID, the gateway emits opaque `/runs/{id}/artifacts/{token}` links and streams them.
Artifact routes check namespace/run ownership. Targets are recorded from backend
responses, never supplied as fetch URLs by a client. Redirects are not followed.
HTTP Range and selected content headers are preserved.

S3 outputs require an explicit backend `s3` configuration, for example:

```yaml
s3:
  endpoint_url: http://seaweedfs-s3.seaweedfs.svc:8333
  region: us-east-1
  access_key_env: ARTIFACT_ACCESS_KEY
  secret_key_env: ARTIFACT_SECRET_KEY
  allowed_prefixes:
    - s3://tenant-a-results/workflows/
```

Set allowed prefixes to actual trusted output locations, with a trailing slash;
use tenant-specific credentials where available. The example bucket is a placeholder,
not provisioned by the gateway. Only backend-reported references under those
prefixes receive gateway links. Trailing-slash S3 directory URLs return a JSON list
of linked files, limited to 10000 entries; objects are streamed. Unsupported file
schemes/origins remain in metadata and are not fetched. File outputs at such
locations do not satisfy the through-gateway byte-retrieval acceptance check until
an appropriate storage integration is configured. Local `file://` artifacts cannot
be read from the gateway's filesystem on behalf of Toil.

Namespace ownership checks do not authenticate callers. Place the gateway behind
the intended authentication/authorization layer before exposing tenant services.
OIDC/JWT and identity-based namespace RBAC remain separate work; the bootstrap's
shared S3 credentials and privileged workflow execution remain unchanged.
