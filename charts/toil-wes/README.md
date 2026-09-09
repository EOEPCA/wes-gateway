# Toil WES

Standalone Helm chart extracted from the experimental Toil WES implementation in
`zoo-project-dru`. Runs the Toil Workflow Execution Service, with optional Celery
workers, shared storage, and node-level NFS/EFS mounting. The chart has no Helm
dependencies and retains the original pinned Toil 9.4.1 Python 3.13 image.

## Install

From the repository root:

```sh
helm lint ./toil-wes
helm upgrade --install toil-wes ./toil-wes --namespace workflows --create-namespace
kubectl --namespace workflows port-forward service/toil-wes 8080:8080
curl http://localhost:8080/ga4gh/wes/v1/service-info
```

Defaults run one WES server using `--bypass_celery`, a ClusterIP service on port
8080, and a dedicated ServiceAccount with a namespace Role and RoleBinding.
Workflow jobs use the Kubernetes batch system. No object store, broker, ingress,
authentication layer, or other ZOO services are installed.

Default storage is ephemeral: runs and state can be lost when the pod is replaced.
Configure storage and job-store credentials before submitting real workflows.
Successful rendering or a responding service-info endpoint does not establish
that a workflow can execute in your cluster.

## Private container registries

Reference existing registry Secrets in the release namespace:

```yaml
imagePullSecrets:
  - name: registry-credentials
  - name: another-registry-credentials
```

These references are added to the WES and Celery pods and the chart-created
ServiceAccount. Newly created Toil worker pods using that account inherit its
pull Secrets when they do not specify their own list. With
`serviceAccount.create: false`, configure `imagePullSecrets` on the existing
ServiceAccount separately; the chart does not modify it.

Kubernetes uses these Secrets to pull pod images. They are not mounted as files
or passed to Singularity/Apptainer inside the worker; private CWL `dockerPull`
images require separate authentication for that runtime.

## Object storage

For AWS, the defaults leave the endpoint and credential Secret unset. Configure
`awsRegion` and credentials appropriate to your environment. A ServiceAccount
annotation can be supplied through `serviceAccount.annotations`; any identity
setup must also work for the Kubernetes job pods launched by Toil.

For an existing MinIO or other compatible endpoint, adapt
[examples/minio.yaml](examples/minio.yaml):

```sh
helm upgrade --install toil-wes ./toil-wes --namespace workflows --create-namespace \
  -f ./toil-wes/examples/minio.yaml
```

`s3.host` is a hostname or IP, without scheme or port. It is used exactly as
provided; use a fully qualified service name for another namespace. Set
`s3.port`, `s3.useSsl`, and `s3.realaws: false` for a compatible endpoint. The
credential Secret must already exist in the **release namespace**, even if the
object storage service runs elsewhere. Configure its key names through
`s3.credentialsSecret.accessKeyKey` and `secretKeyKey`.

The chart sets endpoint variables in the server and Celery workers and passes
endpoint options to workflow jobs. `env` adds container environment variables;
it is not a general mechanism to propagate every variable to workflow job pods.
`TOIL_APPLIANCE_SELF` defaults to the configured image and can be overridden in
`env` for a custom workflow worker image. Use the dedicated settings for broker
and Secret credentials instead of duplicating those variables in `env`.

## Celery and persistent storage

Celery requires an external broker and storage shared by WES and all Celery
workers. Create a Secret named `toil-broker` with key `broker-url` containing your
full broker URL, and an RWX PVC named `toil-workflows`, then adapt and apply:

```sh
helm upgrade --install toil-wes ./toil-wes --namespace workflows --create-namespace \
  -f ./toil-wes/examples/minio.yaml \
  -f ./toil-wes/examples/celery.yaml
```

Alternatively set `celery.brokerUrl`; it is mutually exclusive with
`celery.brokerSecret.name`. `celery.resultBackend` defaults to `rpc://` as in the
source chart. Choose a backend compatible with your broker. There is no bundled
RabbitMQ or dependency on the ZOO queues.

Set `sharedStorage.create: true` to provision a PVC instead of referencing an
existing one. `sharedStorage.storageClass: ""` uses the cluster's default storage
class, except with NFS static binding below. All `workDir` and `stateStore` paths
must be under `sharedStorage.mountPath`. Multi-node deployments normally require
ReadWriteMany storage. ReadWriteOnce is only appropriate with scheduling that
keeps all consumers on a compatible node. More than one WES replica requires
Celery mode; validate the result backend and multi-server behavior before scaling.

The server and Celery PVC does not automatically mount into the separate workflow
job pods launched by Toil. Configure the job store and worker filesystem access
for your workflows. `hostPath` and the optional NFS integration retain the source
chart's mechanism for providing node storage to those pods.

## Optional NFS/EFS mounting

[examples/nfs.yaml](examples/nfs.yaml) creates a static NFS PV/PVC and enables the
node mounter. Replace the example server and export before applying it. This can
be combined with the Celery example; apply the NFS example last to select a
chart-created PVC.

The retained experimental DaemonSet uses privileged containers and `hostPID` to
mount NFS in the node mount namespace. Nodes need working NFS tooling and access
to the export; its initialization also downloads Alpine NFS packages. It tolerates
all taints and respects `nodeSelector`. Its shutdown handler unmounts the node
path, so a rollout or uninstall can affect active workflows. Use a path dedicated
to this release and plan node-mounter maintenance around running jobs.

`hostPath` takes precedence over `nfsMount.nodeMountPath`. With
`sharedStorage.create: true` and an empty storage class, the chart creates a
namespace-qualified static PV with reclaim policy `Retain`. A nonempty storage
class uses dynamic provisioning instead. The node mounter still runs if enabled.
Retained NFS data and released PVs require administrator lifecycle management.

## Configuration and extraction map

All original `toilWes.*` options are now at the top level in
[values.yaml](values.yaml), except for the service-account changes below.
[values.schema.json](values.schema.json) validates option types; templates check
required broker, claim, endpoint, and shared-path settings.

| Original element in `zoo-project-dru` | Standalone equivalent |
| --- | --- |
| `templates/dp-toil-wes.yaml` | `templates/deployment.yaml` |
| `templates/dp-toil-wes-celery-worker.yaml` | `templates/celery-worker.yaml` |
| `templates/service-toil-wes.yaml` | `templates/service.yaml` |
| `templates/sa-toil-wes.yaml`, processing-manager account | `templates/serviceaccount.yaml`; dedicated account by default |
| `templates/rbac-toil-wes.yaml` | `templates/rbac.yaml` |
| `templates/claim-toil-wes-shared.yaml` | `templates/pvc.yaml` |
| `templates/pv-toil-wes-nfs.yaml` | `templates/nfs-pv.yaml` |
| `templates/ds-toil-wes-nfs-mounter.yaml` | `templates/nfs-mounter.yaml` |
| `files/toil/*.py` | Same runtime patches, with standalone values references |
| Integrated RabbitMQ URL | `celery.brokerUrl` or `celery.brokerSecret` |
| Integrated MinIO service/Secret | Explicit `s3` settings for an existing service/Secret |
| `toilWes.serviceAccountName` | `serviceAccount.name` |
| Unwired `toilWes.serviceAccount` compatibility field | Removed; use `serviceAccount.create` and `serviceAccount.name` |

`rbac.create` controls the namespace Role and RoleBinding. When
`serviceAccount.create: false`, an existing `serviceAccount.name` is required.
The account is used consistently by WES, Celery, and the Kubernetes job options.
The extracted RBAC permissions retain the parent chart's scope, including access
to namespace Secrets. `privileged` controls the jobs Toil launches and defaults
to the source chart's `true` setting.

`resources.defaultMemory/defaultDisk/maxMemory/maxDisk` configure Toil workflow
jobs. Optional `resources.requests` and `resources.limits` configure the WES and
Celery containers. `service.port` changes the service-facing port; the application
continues listening on container port 8080.

To connect the existing ZOO deployment to this chart, disable its
`toilWes.enabled` and set `workflow.inputs.WES_URL` to the new service's
`http://<service>.<namespace>.svc:8080/ga4gh/wes/v1/` endpoint (adjust the service
port if changed). Client credentials and cookiecutter settings remain in ZOO.
The old overlay files include ZOO-only settings and cannot be passed directly to
this chart; migrate their `toilWes` contents as described above. Existing resources
and workflow state are not automatically transferred to the new Helm release.

## Validation and runtime limits

```sh
helm lint ./toil-wes
python3 ./toil-wes/tests/render.py
```

The offline checks require Helm, Python 3, and PyYAML. They cover default, S3,
Celery, and NFS rendering; service/account/storage wiring; naming; embedded shell
and Python syntax; and invalid configurations. They do not deploy to Kubernetes
or execute workflows.

The copied runtime patches modify installed Toil Python files at container startup
for Celery handling and S3 compatibility. They rely on the pinned image's
`/usr/local/lib/python3.13/dist-packages` layout and exact source strings, and may
silently stop matching another image. They affect the server/Celery containers;
they do not rebuild or patch independently launched workflow job images. Treat
image upgrades and the retained NFS integration as requiring cluster-level tests.
