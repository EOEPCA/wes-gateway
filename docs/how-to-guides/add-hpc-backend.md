# Add an HPC-backed WES service

Use this guide to connect an existing HPC-facing WES service to the gateway.
The gateway already supports registration of compatible HTTP WES backends; it
does not submit directly to SLURM or PBS Pro. This procedure configures gateway
routing, not the HPC scheduler or its execution service.

```text
Client → external API gateway (when configured) → WES Gateway
                                               → HPC-facing WES → HPC scheduler
```

An independent Toil WES deployment configured for the HPC environment can provide
this interface. Another compatible WES implementation can also be used. The
bundled Toil chart configures Kubernetes execution; registering a new URL does not
convert that deployment into an HPC backend.

## Prepare the HPC execution service

Work with the HPC operator to provide:

- A WES API root reachable from the gateway pod, with a trusted HTTPS certificate
  and any required service credentials.
- A workflow executor configured and permitted to use the scheduler, account,
  partition or queue, and resource limits.
- A supported workflow runtime and container execution method, together with
  work directories and storage accessible to the execution nodes.
- Input data access and a way to expose logs and outputs to workflow clients.

Validate a small workflow directly through that WES service before registering
it. Record its supported workflow types and versions, execution requirements,
and cancellation behavior. HPC scheduler setup and ESA access arrangements are
specific to the target facility and are not supplied by this repository.

## Register the service and logical namespace

Edit the complete registry used by your deployment. For the bundled installation,
this is `config/backends.yaml`. Keep all existing entries and add the following
backend and namespace mappings:

```yaml
# Fragment to merge into your existing registry.
backends:
  toil-hpc:
    type: toil
    base_url: https://hpc-wes.example.org/ga4gh/wes/v1
    bearer_token_env: HPC_WES_TOKEN
    verify_tls: true
    connect_timeout: 10
    read_timeout: 60
namespaces:
  hpc:
    backend: toil-hpc
```

Replace the placeholder URL with the service's actual API root. Use `type: wes`
for a compatible service other than Toil. The complete registry must retain
`version: 1` and all existing namespace mappings, backend entries and settings.
See the [configuration reference](../reference/configuration.md#registry) for
supported fields.

Clients now select this execution service using `/wes/v1/hpc`. The name `hpc`
does not automatically select a scheduler partition or account. Configure that
execution domain at the backend. To expose several domains, register separately
configured WES services and map logical namespaces to them. Mapping several
namespaces to one service does not create distinct scheduler identities.

## Supply backend credentials

If the service requires a bearer token, provision Secret `hpc-wes-credentials`
with key `token` in the gateway namespace using your secret-management process.
Add this entry to a Helm values file, retaining any existing `extraEnv` entries:

```yaml
extraEnv:
  - name: HPC_WES_TOKEN
    valueFrom:
      secretKeyRef:
        name: hpc-wes-credentials
        key: token
```

Save the values as `hpc-values.yaml` for the commands below. Omit both the registry's
`bearer_token_env` and this environment entry if bearer authentication is not
required. The configured token authenticates the gateway to the HPC WES service;
it is not the workflow user's identity. The gateway does not automatically forward
client authorization headers or acquire and refresh federated access tokens.
If the facility requires user delegation or a different authentication mechanism,
resolve that integration before using this registration.

Client-facing OIDC and namespace permissions belong to the external API gateway
and policy layer, for example OPA. If present, update that layer's policies for
`hpc` and cover all WES operations and artifacts. See
[identity and run ownership](../explanation/c4/target-hybrid.md#identity-and-run-ownership).

## Apply the configuration

For a Helm-managed gateway, run from the repository root:

```sh
helm lint charts/wes-gateway \
  --values hpc-values.yaml \
  --set-file backendConfig=config/backends.yaml

helm upgrade wes-gateway charts/wes-gateway \
  --namespace wes-gateway --reuse-values \
  --values hpc-values.yaml \
  --set-file backendConfig=config/backends.yaml \
  --wait --timeout 5m

kubectl rollout status deployment/wes-gateway -n wes-gateway --timeout=180s
```

Substitute your registry file path as needed and omit `--values hpc-values.yaml`
if no extra values are needed. Helm receives the complete registry, not the
fragment above. Credentials and stored backend bindings are checked at gateway
startup; inspect pod logs if it fails to become ready.

If Skaffold manages this release, add `hpc-values.yaml` to the **wes-gateway**
release's `valuesFiles` in `skaffold.yaml`, and apply using that workflow instead
of a concurrent manual Helm upgrade. Its existing `setFiles.backendConfig` reads
`config/backends.yaml`. This adds gateway configuration only; Skaffold does not
install an HPC-facing WES service for you.

## Verify routing and workflow execution

For the bundled local port forward:

```sh
export GATEWAY_URL=http://localhost:8090
export WES_URL="$GATEWAY_URL/wes/v1/hpc"

curl --fail-with-body -sS --max-time 60 "$WES_URL/service-info" | jq .
curl --fail-with-body -sS --max-time 60 "$WES_URL/runs" | jq .
```

For a protected installation, use its external API gateway URL and the required
client access token instead. Successful service information confirms HTTP routing,
not scheduler execution. A new namespace can list no runs even if work was
previously submitted directly to the backend.

Follow [Run your first workflow](../tutorials/submit-and-monitor-cwl.md) with
`NAMESPACE=hpc` and your gateway URL, provided the backend supports the example's
CWL version and container requirements. Then use the
[scatter example](submit-workflow-runs.md#run-the-supplied-scatter-workflow).
For each workflow, retain its gateway run ID and verify completion, expected
outputs and available logs. Use [Monitor and cancel runs](monitor-and-cancel-runs.md)
to verify listing, details, status and cancellation of a suitable long-running job.

The gateway cannot read a file that exists only on an HPC filesystem. Backend log
and output locations must be accessible through supported retrieval mechanisms.
S3 output retrieval requires explicit
[artifact configuration](configure-backends.md#enable-retrieval-of-s3-outputs).
Inputs must already be accessible to the executor; artifact retrieval does not
stage inputs or synchronize cloud and HPC storage.

## Resolve common integration failures

| Symptom | Action |
| --- | --- |
| Unknown `hpc` namespace | Check the mounted complete registry and completed rollout |
| Backend timeout or connection error | Check DNS, firewall rules and connectivity from the gateway pod |
| Backend authentication or TLS failure | Check the backend token and certificate trust; distinguish this from client-facing policy rejection |
| Run remains queued | Inspect scheduler capacity, account permissions, partition/queue and resource requests with the HPC operator |
| Execution fails | Inspect backend logs, runtime compatibility, input access and work-directory permissions |
| Logs or outputs are metadata only | Expose supported artifact locations; HPC-local paths are not readable by the gateway |

Keep the backend ID and API root stable while gateway records refer to it. Follow
[backend replacement guidance](add-backends.md#existing-runs-shared-backends-and-replacement)
when changing the execution service.
