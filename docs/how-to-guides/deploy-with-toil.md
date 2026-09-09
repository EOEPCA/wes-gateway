# Deploy the gateway with Toil WES

Use this guide to deploy the gateway in front of an existing Toil WES service on
Kubernetes. You will register Toil as the first backend and expose it under the
logical namespace `tenant-a`. See the [deployment diagram and component roles](../explanation/architecture.md#deployment-boundaries)
for how the gateway connects to Toil and metadata storage.

To install Toil and its supporting services together with the gateway, use
[Deploy the complete stack with Skaffold](deploy-stack-with-skaffold.md).

## Before you begin

You need:

- Helm and kubectl access to the target Kubernetes cluster.
- A gateway container image accessible to that cluster, including any required
  image-pull credentials.
- A running Toil WES service and its complete WES API URL.
- A default StorageClass, or an existing PVC in the gateway namespace.
- A checkout or distribution containing `charts/wes-gateway` and
  `examples/deployment`. Run commands from its root directory.

The gateway chart does not install Toil or its execution infrastructure. This
example assumes Toil Service `toil-wes` on port 8080 in `tenant-a`. Deploy Toil using
its own deployment instructions before proceeding. The gateway does not need
Kubernetes permissions to manage workflow pods.

## Check the Toil service

```sh
kubectl config current-context
kubectl get deployment,service,pod,pvc -n tenant-a
kubectl rollout status -n tenant-a deployment/toil-wes --timeout=180s
```

Adapt the Service and namespace below to match your installation. The backend URL
must be reachable from the gateway pod; a workstation's localhost port forward is
not a suitable URL for a gateway deployed inside Kubernetes.

## Register Toil

Use `examples/deployment/toil-backends.yaml` for a fresh installation:

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

`toil-a` is the backend ID. `tenant-a` under `namespaces` is the name clients use
in `/wes/v1/tenant-a`. The backend URL includes Toil's `/ga4gh/wes/v1` prefix.

For an existing gateway, extend its complete registry instead of replacing it with
this single-backend example. Retain registrations referenced by existing runs.
See [Add backends](add-backends.md) for that procedure.

## Set storage and image values

The supplied `examples/deployment/gateway-values.yaml` configures one replica and
a 1 GiB SQLite PVC. Edit it for your environment:

- Set `persistence.storageClass` when there is no suitable default class.
- Set `persistence.existingClaim` to use an externally managed PVC. Use this option
  when metadata must survive removal of the Helm release; chart-created PVCs are
  removed on uninstall.
- Set `imagePullSecrets` if your image requires registry credentials. The Secret
  must exist in the gateway namespace.

Set the image reference supplied for your deployment:

```sh
export IMAGE=YOUR_REGISTRY/wes-gateway:YOUR_TAG
```

See [configuration reference](../reference/configuration.md) for supported chart
values. For multiple replicas, [configure shared PostgreSQL metadata](configure-backends.md#use-postgresql-for-shared-metadata).

## Install with Helm

```sh
helm lint charts/wes-gateway \
  --values examples/deployment/gateway-values.yaml \
  --set-file backendConfig=examples/deployment/toil-backends.yaml

helm upgrade --install wes-gateway charts/wes-gateway \
  --namespace wes-gateway --create-namespace \
  --values examples/deployment/gateway-values.yaml \
  --set-string image.ref="$IMAGE" \
  --set-file backendConfig=examples/deployment/toil-backends.yaml \
  --wait --timeout 5m
```

The chart installs a Deployment, Service, ServiceAccount, ConfigMap and, unless an
existing claim is selected, a metadata PVC. `--set-file backendConfig` supplies
the entire registry. Apply later changes with the same values and registry files.
Changing the effective registry triggers a pod rollout.

## Check the deployment

```sh
helm status wes-gateway --namespace wes-gateway
kubectl get deployment,pod,service,pvc -n wes-gateway
kubectl rollout status deployment/wes-gateway -n wes-gateway --timeout=180s
```

Open a port forward in a separate terminal:

```sh
kubectl port-forward -n wes-gateway service/wes-gateway 8090:8090
```

In your working terminal, check readiness and Toil connectivity:

```sh
export WES_URL=http://localhost:8090/wes/v1/tenant-a
curl --fail-with-body -sS --max-time 60 http://localhost:8090/readyz
curl --fail-with-body -sS --max-time 60 "$WES_URL/service-info"
```

Readiness confirms access to gateway metadata storage. Service information confirms
HTTP routing to Toil. Neither check guarantees workflow execution.

Continue with [Run your first workflow](../tutorials/submit-and-monitor-cwl.md) to
submit Hello World and retrieve its result. For an error during deployment or
routing, use [Troubleshooting](troubleshoot.md).
