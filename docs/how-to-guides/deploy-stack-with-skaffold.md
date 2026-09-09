# Deploy the complete stack with Skaffold

Use this guide to install the gateway together with two Toil WES tenants,
RabbitMQ, and SeaweedFS. All local deployment files are included in this
repository; a separate `toil-bootstrap` checkout is not required.

For a gateway in front of an already managed Toil service, use
[Deploy with Toil WES](deploy-with-toil.md) instead.

## Prepare the cluster

You need Docker access for the gateway image build, Helm, kubectl, and Skaffold v2
with `skaffold/v4beta11` support. Select your intended Kubernetes context before
running commands from this repository's root directory:

```sh
kubectl config current-context
kubectl get storageclass
```

The included values retain the bootstrap's `standard` storage class and
ReadWriteMany claims for Toil. SeaweedFS also uses `standard`; RabbitMQ and the
gateway use the cluster's default storage class. For a different cluster, update
`deploy/toil/toil-wes.yaml` and `deploy/toil/seaweedfs.yaml` to use its storage
classes. The stack requests 66 GiB of persistent storage in total.

Images and the pinned remote SeaweedFS and RabbitMQ charts require network access.
For a remote cluster, supply a registry reachable by its nodes using Skaffold's
`--default-repo YOUR_REGISTRY` option. For Minikube, Skaffold detects the local
cluster and handles the built gateway image.

## Review deployment values

| File | Configure |
| --- | --- |
| `config/backends.yaml` | Gateway routing to the two Toil tenant Services |
| `deploy/toil/toil-wes.yaml` | Toil shared storage, S3 connection, Celery, image-pull Secrets |
| `deploy/toil/seaweedfs.yaml` | S3 service and persistent storage |
| `deploy/toil/rabbitmq.yaml` | Broker storage and tenant definitions import |
| `charts/toil-bootstrap/values.yaml` | Shared S3 credentials and per-tenant RabbitMQ credentials |
| `skaffold.yaml` | Release names, namespaces, pinned remote chart versions and port forwards |

The credential values are demonstration defaults. Replace them before exposing
this stack to other users. Updating a Secret alone does not rotate credentials
already stored in RabbitMQ. The bundled execution configuration uses privileged
workers and shared S3 credentials; configure your access controls accordingly.

Release names and namespaces match the original bootstrap. If those releases
already exist, this configuration updates them in place. Stop any other Skaffold
process managing the same releases before starting this one. Existing PVC access
modes and storage classes cannot be changed in place by a Helm upgrade.

## Deploy and connect

```sh
skaffold run --port-forward
```

Skaffold builds the gateway image, installs credential Secrets, then SeaweedFS,
RabbitMQ, the two Toil tenants, and the gateway. It waits for each Helm release.
Keep the command running to retain the port forwards.

To watch configuration changes and redeploy automatically, use the following
command instead:

```sh
skaffold dev --port-forward
```

| Endpoint | Local address |
| --- | --- |
| Gateway tenant A | `http://localhost:8090/wes/v1/tenant-a` |
| Gateway tenant B | `http://localhost:8090/wes/v1/tenant-b` |
| Gateway interactive API documentation | `http://localhost:8090/docs` |
| Direct Toil tenant A / B | `http://localhost:8080/ga4gh/wes/v1` / `http://localhost:8081/ga4gh/wes/v1` |
| S3 | `http://localhost:8333` |
| RabbitMQ management | `http://localhost:15672` |

Check routing through the gateway:

```sh
curl --fail-with-body -sS http://localhost:8090/readyz
curl --fail-with-body -sS http://localhost:8090/wes/v1/tenant-a/service-info
curl --fail-with-body -sS http://localhost:8090/wes/v1/tenant-b/service-info
```

Continue with [Run your first workflow](../tutorials/submit-and-monitor-cwl.md).
For pending PVCs, failed pods, routing errors, or failed runs, use the
[troubleshooting guide](troubleshoot.md).

## Remove the stack

```sh
skaffold delete
```

This configuration owns all nine releases, so deletion removes the gateway and
Toil stack together. Exiting `skaffold dev` also cleans up its deployed releases
by default. Chart-created gateway and Toil PVCs are removed; StatefulSet PVCs may
remain. Preserve needed metadata and workflow data before cleanup. Use an
[externally managed gateway claim](configure-backends.md#keep-sqlite-metadata-across-release-removal)
when gateway run associations must survive release removal.
