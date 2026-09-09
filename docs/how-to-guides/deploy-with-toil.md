# Deploy the gateway with Toil WES as the first backend

This guide deploys the gateway in front of a separately installed Toil WES service
on Kubernetes. It registers one Toil backend, exposes the logical namespace
`tenant-a`, and checks requests through the gateway. Toil continues to manage
workflow execution; the gateway adds the HTTP entrypoint and durable run routing.

## Deployment diagram

![Gateway Helm deployment and Toil backend connections](../diagrams/out/overall.svg)

The diagram shows the two-tenant bootstrap layout. This guide initially registers
only tenant A. Follow [Add additional backends](add-backends.md) to register
tenant B or another WES service after deployment.

| Component | Kubernetes namespace | Responsibility |
| --- | --- | --- |
| Gateway Service and Deployment | `wes-gateway` | Public WES routes on port 8090 |
| Backend ConfigMap | `wes-gateway` | Logical namespace to backend URL mapping |
| Gateway SQLite PVC | `wes-gateway` | Gateway run IDs, namespace ownership and original backend IDs |
| Toil WES Service and Deployment | `tenant-a` | WES API on port 8080 at `/ga4gh/wes/v1` |
| Toil Celery workers and workflow pods | `tenant-a` | Workflow execution |
| RabbitMQ and SeaweedFS | `rabbitmq`, `seaweedfs` | Bootstrap execution queue and workflow storage |

The gateway chart does not install Toil, RabbitMQ, or SeaweedFS. Gateway metadata
and Toil workflow storage are separate. The gateway does not need Kubernetes RBAC
permissions to create workflow pods and does not validate caller identity; configure
the intended external authentication/authorization layer before exposing it to users.

## 1. Prepare Toil and the deployment environment

You need Docker build access, Helm, kubectl, and access to a Kubernetes cluster.
Skaffold is needed only for the development alternative below. The cluster needs
storage for the gateway's 1 GiB PVC and the Toil stack's own volumes. Run gateway
commands from the **wes-gateway repository root**.

The existing `toil-bootstrap` checkout used for this integration is at
`/data/work/git-terradue-com/fbrito/toil-bootstrap`. If the stack is not already
installed, configure its storage and credentials following that checkout's
`docs/tutorials/first-deployment.md`, then deploy it in a separate terminal:

```sh
cd /data/work/git-terradue-com/fbrito/toil-bootstrap
skaffold run --port-forward
```

Replace the path for your environment. The bootstrap configures both tenant A and
tenant B. Its WES/Celery storage requires an RWX-capable StorageClass; the gateway's
single-replica SQLite PVC uses ReadWriteOnce. The gateway chart does not configure
or repair Toil's storage, image-pull credentials, or broker configuration.

Verify that you are using the intended cluster and that tenant A is ready:

```sh
kubectl config current-context
kubectl get deployment,service,pod,pvc -n tenant-a
kubectl rollout status -n tenant-a deployment/toil-wes --timeout=180s
kubectl rollout status -n tenant-a deployment/toil-wes-celery --timeout=180s
```

The example assumes Service `toil-wes`, port 8080, in `tenant-a`. Substitute the
actual Service and namespace in the backend registration if your deployment differs.

## 2. Register the first Toil backend

The checked-in `examples/deployment/toil-backends.yaml` contains:

```yaml
version: 1
backends:
  toil-a:
    type: toil
    base_url: http://toil-wes.tenant-a.svc:8080/ga4gh/wes/v1
    connect_timeout: 10
    read_timeout: 60
    keepalive_expiry: 1
    verify_tls: true
namespaces:
  tenant-a:
    backend: toil-a
```

`toil-a` is a stable backend ID. `tenant-a` under `namespaces` is a logical API
namespace; it selects that ID. The logical name does not have to match a Kubernetes
namespace, although it does in this example. The `base_url` includes Toil's API
prefix and uses cluster DNS because the gateway will run inside Kubernetes.

This file replaces the chart registry **in full** when passed with `--set-file`.
Use it for a fresh gateway database. On an existing gateway with recorded runs,
retain every backend registration those records reference. The repository's
`config/backends.yaml` registers both tenants and can be used instead without
removing tenant B. Changing a used backend ID's URL or removing it causes startup
to fail; add a new ID for a new target.

Backend registration is configuration, not an API POST. The application validates
the full registry on startup. Unknown namespace mappings and invalid settings
produce explicit startup errors. See [registry settings](configure-backends.md#registry-contract)
for credentials, TLS and optional S3 artifact configuration.

## 3. Configure and deploy the Helm chart

The example `examples/deployment/gateway-values.yaml` uses one replica and a 1 GiB
SQLite PVC. Set `persistence.storageClass` if the cluster has no default class.
For metadata that must survive Helm uninstall or Skaffold cleanup, provision a PVC
outside the release and set `persistence.existingClaim` to its name. The chart's
own PVC is removed on uninstall.

Build and push an image to a registry your cluster can pull from. Replace the
placeholder image name before running these commands:

```sh
export IMAGE=YOUR_REGISTRY/wes-gateway:YOUR_TAG

docker build --tag "$IMAGE" .
docker push "$IMAGE"
```

For a private registry, configure the chart's `imagePullSecrets` with a pull Secret
in `wes-gateway`. For a local Minikube development image, use the Skaffold alternative
below to build with the local cluster runtime.

Validate, preview, and install:

```sh
mkdir -p output/deployment

helm lint charts/wes-gateway \
  --values examples/deployment/gateway-values.yaml \
  --set-file backendConfig=examples/deployment/toil-backends.yaml

helm template wes-gateway charts/wes-gateway \
  --namespace wes-gateway \
  --values examples/deployment/gateway-values.yaml \
  --set-string image.ref="$IMAGE" \
  --set-file backendConfig=examples/deployment/toil-backends.yaml \
  > output/deployment/manifests.yaml

helm upgrade --install wes-gateway charts/wes-gateway \
  --namespace wes-gateway --create-namespace \
  --values examples/deployment/gateway-values.yaml \
  --set-string image.ref="$IMAGE" \
  --set-file backendConfig=examples/deployment/toil-backends.yaml \
  --wait --timeout 5m
```

The chart mounts the registry at `/app/config/backends.yaml`, sets
`WES_BACKENDS_CONFIG` and `WES_DATABASE_URL`, and runs `wes_api_gateway.main:app`.
A registry checksum on the pod template triggers rollout when the effective config
changes. Apply configuration updates with the same Helm command; there is no
in-process hot reload. More than one replica requires shared PostgreSQL metadata
storage; see [database configuration](configure-backends.md#deploy-with-helm-through-skaffold).

### Development alternative: Skaffold

For the repository's existing two-tenant registry, use this instead of the direct
Helm/image-build commands:

```sh
skaffold dev --port-forward
```

Skaffold builds the Dockerfile, injects the built image into Helm, and supplies
`config/backends.yaml` as `backendConfig`. It deploys the same `wes-gateway` release,
forwards port 8090, and watches files. Keep both configured backends in this file
for the existing two-tenant deployment. On a fresh deployment where only tenant A
is wanted, edit that file to match the single-backend example before starting.
Do not run competing Skaffold and manual Helm upgrades against the same release.

## 4. Verify routing through the gateway

Check the installed release and workload:

```sh
helm status wes-gateway --namespace wes-gateway
kubectl get deployment,pod,service,pvc -n wes-gateway
kubectl rollout status deployment/wes-gateway -n wes-gateway --timeout=180s
```

For direct Helm deployment, open a port forward in a separate terminal. Skip this
if Skaffold is already forwarding port 8090:

```sh
kubectl port-forward -n wes-gateway service/wes-gateway 8090:8090
```

Use curl and jq in your working terminal:

```sh
export GATEWAY_URL=http://localhost:8090
export WES_URL="$GATEWAY_URL/wes/v1/tenant-a"

curl --fail-with-body -sS --max-time 60 "$GATEWAY_URL/readyz" | jq .
curl --fail-with-body -sS --max-time 60 "$WES_URL/service-info" |
  jq '{supported_wes_versions, workflow_type_versions}'
curl --fail-with-body -sS --max-time 60 "$WES_URL/runs" | jq .
```

Readiness checks the gateway's metadata database; service-info checks routing to
Toil. A fresh database legitimately returns `{"workflows":[],"next_page_token":""}`.
Neither check proves that Toil can execute a workflow.

Complete the [curl workflow tutorial](../tutorials/submit-and-monitor-cwl.md) to
submit Hello World, verify `COMPLETE`, retrieve logs and output, and cancel a
running sleep workflow. Swagger UI is at
[http://localhost:8090/docs](http://localhost:8090/docs). The API contract and
historical execution evidence are in [API reference](../reference/api.md) and
[integration results](../reference/integration-results.md).

## Troubleshooting

### Gateway does not start or become ready

```sh
kubectl get pods,pvc -n wes-gateway
kubectl describe deployment wes-gateway -n wes-gateway
kubectl get events -n wes-gateway --sort-by=.metadata.creationTimestamp
kubectl logs -n wes-gateway deployment/wes-gateway --tail=100
```

| Symptom | Check and correction |
| --- | --- |
| Docker socket permission denied before deployment | Verify the login session has Docker group membership. If already registered, a new login or `sg docker -c 'skaffold dev --port-forward'` activates it for the command. |
| `ImagePullBackOff` | Check the rendered image reference, registry reachability and pull Secret. Confirm the built image was pushed or loaded into the cluster runtime. |
| PVC remains `Pending` | Check the StorageClass/provisioner and requested capacity, or supply a bound existing claim in the gateway namespace. |
| Registry validation error / `CrashLoopBackOff` | Read gateway logs for the failing field. Check duplicate YAML keys, backend IDs, namespace references, URLs and required credential environment variables. |
| Backend has recorded runs / identity changed | Restore its original ID/type/URL. Register a different target under a new backend ID; do not erase metadata to bypass validation. |
| `/readyz` fails or HTTP 503 | Check database availability, PVC mounting, filesystem ownership and database Secret settings. SQLite needs writable `/data` and one replica. |

The ConfigMap and Deployment show which configuration and image Helm installed:

```sh
kubectl get configmap wes-gateway-backends -n wes-gateway \
  -o jsonpath='{.data.backends\.yaml}'
kubectl get deployment wes-gateway -n wes-gateway \
  -o jsonpath='{.spec.template.spec.containers[0].image}'
```

The resource names above assume the default Helm release and naming values.
Backend credentials should be Secret references, not embedded in registry URLs.

### Namespace or run routing fails

| Response or behavior | Interpretation and next action |
| --- | --- |
| 404 `Unknown WES namespace` | Check `/wes/v1/tenant-a`, exact spelling/case, and the mounted registry's `namespaces`. Reapply the Helm config and wait for rollout. |
| 404 `Run not found in namespace` | Use the gateway ID returned by submission and its original logical namespace. Raw Toil IDs and IDs from a separate gateway database will not resolve. |
| Empty listing / recently submitted run missing from first page | Listings are oldest first and limited to the current gateway database/namespace. Follow `next_page_token` or use the saved run URL directly. |
| 400 invalid page token | Keep the token with its original namespace and use curl `--data-urlencode`. Start with no token after switching namespaces. |
| 502 transport failure or 504 timeout | Verify Toil Service endpoints, cluster DNS, gateway-to-Toil network access and backend health. A healthy gateway probe alone does not check Toil. |
| Backend 404 from service-info or other operations | Check `base_url` includes `/ga4gh/wes/v1` once and points to the WES Service, not a worker. Task endpoints may simply be unsupported. |

Check Service endpoints and test the configured tenant A URL **from the gateway
pod**, rather than substituting a localhost URL inside Kubernetes:

```sh
kubectl get endpointslices -n tenant-a \
  -l kubernetes.io/service-name=toil-wes

kubectl exec -n wes-gateway deployment/wes-gateway -- python -c \
  'import urllib.request; r = urllib.request.urlopen("http://toil-wes.tenant-a.svc:8080/ga4gh/wes/v1/service-info", timeout=10); print(r.status)'
```

This diagnostic is for the example's unauthenticated Toil HTTP service. If your
backend requires credentials, use its configured authentication when diagnosing it.
For intermittent `RemoteProtocolError` with Toil, check `keepalive_expiry`; the
one-second default resolved the idle-connection failures observed during validation.

### Submission or workflow execution fails

A failed HTTP submission and a successfully submitted run in `EXECUTOR_ERROR` are
different failures. Keep the HTTP response and gateway run ID before investigating.

- HTTP 400: check required WES form fields, JSON object values, CWL version, and
  attachment names. `workflow_params=<inputs.json` sends JSON as a text field;
  `workflow_attachment=@workflow.cwl` uploads the workflow file.
- Submission timeout or `gateway_run_id` with unknown outcome: do not resubmit
  automatically. Toil may already have accepted the work. Follow
  [run recovery](configure-backends.md#namespace-ownership-and-run-recovery).
- `EXECUTOR_ERROR` or `SYSTEM_ERROR`: inspect run detail and available stderr,
  then Toil/Celery and execution pod diagnostics. Check input access, workflow
  syntax, container images, storage, broker connectivity and execution resources.

```sh
export RUN_ID=YOUR_GATEWAY_RUN_ID
mkdir -p output/troubleshooting
curl --fail-with-body -sS --max-time 60 "$WES_URL/runs/$RUN_ID" \
  --output output/troubleshooting/run.json
jq '{state, request, run_log, task_logs, outputs}' output/troubleshooting/run.json
STDERR_URL=$(jq -r '.run_log.stderr // empty' output/troubleshooting/run.json)
if [ -n "$STDERR_URL" ]; then
  curl --fail-with-body -sS --max-time 60 "$STDERR_URL" \
    --output output/troubleshooting/stderr.txt
fi

kubectl get pods -n tenant-a
kubectl logs -n tenant-a deployment/toil-wes --tail=100
kubectl logs -n tenant-a deployment/toil-wes-celery --tail=100
kubectl get pods -n rabbitmq
kubectl get pods -n seaweedfs
```

Review logs before sharing them: raw Toil logs can include deployment command
arguments and workflow data. A SeaweedFS `UploadPart` InternalError occurred during
early overlapping test runs; sequential reruns succeeded. Investigate the actual
storage error rather than treating every execution failure as a gateway routing bug.

### Logs, outputs or cancellation do not behave as expected

Use log URLs from the gateway run-detail response. A `404` artifact response can
mean the token belongs to a different run/namespace/database. An upstream retrieval
error can mean the artifact is unavailable or removed. S3 File/Directory output
retrieval needs explicit allowed prefixes and credentials; unsupported locations
remain metadata. See [logs and output files](configure-backends.md#logs-and-output-files).

Cancellation is asynchronous. Poll until `CANCELED` or another terminal state;
`CANCELING` is not proof of completion. The evaluated Toil deployment could remain
at `CANCELING` when cancellation was requested while QUEUED. Running-workflow
cancellation passed in both tenants. Check the original backend state and workers;
do not change the gateway's reported state to manufacture success.
