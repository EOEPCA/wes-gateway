# Add additional WES backends

Add a backend entry and a logical namespace mapping to the gateway registry, then
apply the configuration. No new gateway route code or registration API call is
needed for a compatible WES HTTP service.

This guide assumes the gateway is already deployed with Toil. For initial setup,
see [Deploy with Toil WES](deploy-with-toil.md).

## 1. Deploy and identify the new WES service

Deploy the additional backend independently. The gateway chart does not create WES
servers or their execution infrastructure. Record the backend's complete WES base
URL, supported workflow types, and any authentication requirements.

For example, another Toil deployment might expose:

```text
http://toil-wes.tenant-c.svc:8080/ga4gh/wes/v1
```

This example assumes Service `toil-wes` in Kubernetes namespace `tenant-c`; replace
it with the actual service address. The gateway must be able to resolve and reach
that URL from its pod. Do not use your workstation's localhost port-forward URL
in a registry mounted inside Kubernetes.

## 2. Extend the registry without removing existing entries

Skaffold reads `config/backends.yaml`. Keep its existing settings, backend IDs,
and namespace mappings, and add the new entries. For the repository's default
two-tenant registry, adding Toil tenant C looks like this:

```yaml
version: 1
backends:
  toil-a:
    type: toil
    base_url: http://toil-wes.tenant-a.svc:8080/ga4gh/wes/v1
  toil-b:
    type: toil
    base_url: http://toil-wes.tenant-b.svc:8080/ga4gh/wes/v1
  toil-c:
    type: toil
    base_url: http://toil-wes.tenant-c.svc:8080/ga4gh/wes/v1
    connect_timeout: 10
    read_timeout: 60
    keepalive_expiry: 1
namespaces:
  tenant-a:
    backend: toil-a
  tenant-b:
    backend: toil-b
  research:
    backend: toil-c
```

Here `toil-c` is the backend's stable ID, `tenant-c` is its Kubernetes namespace,
and `research` is the logical name used by clients:

```text
http://localhost:8090/wes/v1/research/runs
```

Logical namespace names are case-sensitive. The gateway accepts IDs of 1–63
letters, digits, dots, underscores or hyphens, starting with a letter or digit.
Choose names that are stable for your clients. Preserve any existing registry-wide
settings, such as `default_namespace` or `max_upload_bytes`, when editing the file.

### Register a different WES implementation

Use `type: wes` for another compatible WES HTTP server. Add this entry under
`backends` and a corresponding entry under `namespaces` in the complete registry:

```yaml
backends:
  hpc-wes:
    type: wes
    base_url: https://wes.example.org/ga4gh/wes/v1
namespaces:
  hpc:
    backend: hpc-wes
```

The URL is a placeholder. Use the service's actual API root; it need not use
Toil's path prefix. Supported adapter types are currently `toil` and `wes`, both
using the HTTP WES transport. A scheduler such as SLURM is not itself a WES backend;
it needs a WES service in front of it. Backend capability and response compatibility
must be checked before assuming your existing workflows will execute there.

### Optional backend authentication

For a backend requiring a bearer token, add `bearer_token_env: HPC_WES_TOKEN` to
its backend entry. Supply that environment variable through the Helm chart's
`extraEnv`, referencing a Secret in the gateway namespace:

```yaml
extraEnv:
  - name: HPC_WES_TOKEN
    valueFrom:
      secretKeyRef:
        name: hpc-wes-credentials
        key: token
```

Create the Secret with your deployment's secret-management process before the pod
starts. Keep tokens out of registry URLs. Preserve existing `extraEnv` entries:
Helm replaces lists rather than appending to them. The gateway fails startup if a
referenced credential environment variable is missing.

If using Skaffold, add the Helm values file containing `extraEnv` to the release's
`valuesFiles` in `skaffold.yaml`. For direct Helm, pass it with `--values` during
the upgrade below. See [configuration options](configure-backends.md#registry-contract)
for TLS, timeouts, and backend-specific S3 artifact access. Client authorization
headers are not automatically forwarded to backends.

## 3. Validate and apply the change

From the repository root, validate the chart with the full updated registry:

```sh
helm lint charts/wes-gateway --set-file backendConfig=config/backends.yaml
```

For full application-level registry validation, use the project's installed Python
environment. Set any referenced credential environment variables first:

```sh
.venv/bin/python -c \
  'from wes_api_gateway.config import load_registry; load_registry("config/backends.yaml"); print("Registry valid")'
```

This checks configuration and credential references, not backend connectivity or
compatibility with existing database bindings. Those bindings are checked when the
gateway starts. If you have not installed the Python environment, follow the
[local tooling instructions](configure-backends.md#run-the-gateway-as-a-local-python-process) or inspect
the application startup logs after deployment.

Choose the deployment method already managing the release:

- **Skaffold dev:** save `config/backends.yaml` and wait for Skaffold to redeploy.
  Inspect its output for deployment completion. Do not also perform a manual Helm
  upgrade while Skaffold is managing the same release.
- **Direct Helm:** update the existing release, preserving its current image and
  other Helm values:

```sh
helm upgrade wes-gateway charts/wes-gateway \
  --namespace wes-gateway \
  --reuse-values \
  --set-file backendConfig=config/backends.yaml \
  --wait --timeout 5m
```

Add `--values YOUR_VALUES_FILE` if you also need to change settings such as
`extraEnv`. `backendConfig` replaces the registry in full; do not pass only the
new backend fragment. If you manage the registry directly through Helm `registry`
values instead, clear any previous `backendConfig` override and supply a complete,
reviewed registry, accounting for Helm's recursive map merging.

The changed registry updates the Deployment's checksum annotation and rolls the
pod. There is no in-process hot reload. For a local Python gateway instead of
Helm, edit the file named by `WES_BACKENDS_CONFIG` and restart that process, keeping
its existing `WES_DATABASE_URL`.

```sh
kubectl rollout status deployment/wes-gateway -n wes-gateway --timeout=180s
kubectl logs -n wes-gateway deployment/wes-gateway --tail=50
```

## 4. Verify the new namespace and existing routes

With the gateway port-forward active, check the new namespace and an existing one:

```sh
export GATEWAY_URL=http://localhost:8090
export WES_URL="$GATEWAY_URL/wes/v1/research"

curl --fail-with-body -sS --max-time 60 "$WES_URL/service-info" |
  jq '{supported_wes_versions, workflow_type_versions, workflow_engine_versions}'
curl --fail-with-body -sS --max-time 60 "$WES_URL/runs" | jq .

curl --fail-with-body -sS --max-time 60 \
  "$GATEWAY_URL/wes/v1/tenant-a/service-info" | jq .
```

The new namespace initially lists no gateway-owned runs, even if that backend has
runs submitted directly to it. A successful service-info request proves HTTP
routing, not workflow execution. For the Toil example, submit and verify Hello
World through the new namespace using the existing runner:

```sh
.venv/bin/python examples/run_workflow.py \
  "$WES_URL" examples/cwl/hello.cwl examples/cwl/hello.inputs.json \
  --expected examples/cwl/hello.expected.json \
  --evidence output/research-hello
```

Or follow the [curl tutorial](../tutorials/submit-and-monitor-cwl.md), setting
`NAMESPACE=research` when preparing the terminal. For another WES implementation,
first select a workflow type/version reported by that backend. Check status,
outputs and available logs, plus an existing run's status in its original namespace.
See [routing and failed-run troubleshooting](deploy-with-toil.md#troubleshooting)
if any of these checks fail.

## Existing runs, shared backends and replacement

- Adding a new backend/namespace leaves existing runs bound to their original
  backend and logical namespace. Do not remove their registrations.
- Two logical namespaces may map to one backend. Gateway listings and run access
  remain scoped by the recorded namespace; this does not create separate execution
  queues, storage, or caller authentication in that backend.
- To redirect **future** submissions, add a new backend ID and update the logical
  namespace mapping to it. Old runs in that namespace still resolve to the original
  backend, which must remain registered and reachable.
- A backend ID with recorded runs cannot be removed or have its type/base URL
  changed: the gateway rejects that configuration at startup. There is currently
  no automatic backend-retirement or run-migration command.
- Removing a logical namespace makes its run routes inaccessible, even while the
  underlying records remain in the database. Retain that namespace while those
  runs need access.

If an update fails startup, restore the previous complete registry and reapply it
with the same deployment method. Keep the database/PVC; deleting it would lose the
run associations you are trying to preserve.
