# WES Gateway Helm chart

From the repository root, build and deploy with Skaffold:

```sh
skaffold dev --port-forward
```

Skaffold builds `Dockerfile`, supplies the fully qualified image as `image.ref`,
and installs this chart as release `wes-gateway` in namespace `wes-gateway`.
It reads the complete registry from `config/backends.yaml` using Helm `--set-file`.
No Kustomize executable is required.

To install an already-built image directly:

```sh
helm upgrade --install wes-gateway charts/wes-gateway \
  --namespace wes-gateway --create-namespace \
  --set image.ref=YOUR_REGISTRY/wes-gateway:YOUR_TAG \
  --set-file backendConfig=config/backends.yaml \
  --wait
```

The default chart registry also contains the two bootstrap tenants. Set
`backendConfig` to replace it in full, or use `registry` in your own Helm values.
Changing the effective registry changes the Deployment pod-template checksum.

The default single replica uses SQLite on a 1 GiB PVC. Configure
`persistence.storageClass`, `persistence.size`, or `persistence.existingClaim` for
your cluster. A chart-created PVC is deleted when the Helm release is uninstalled
(including Skaffold cleanup); use an externally managed existing claim when data
must survive development teardown. Back up any run metadata you need to retain.

For PostgreSQL, set `database.secretName` and `database.secretKey` to a Secret key
containing a `postgresql+psycopg://...` URL, disable persistence if not needed, and
set `replicaCount`. Secret contents cannot be checked at chart rendering time;
ensure the Secret contains a PostgreSQL URL before using multiple replicas.
Without a Secret, SQLite requires one replica and persistence enabled.

`extraEnv` accepts Kubernetes environment entries, including Secret references for
backend credentials. Configure `imagePullSecrets`, `service`, `serviceAccount`,
`resources`, `nodeSelector`, `tolerations`, and `affinity` through chart values.
The application validates the complete backend registry on startup.

Validation:

```sh
helm lint charts/wes-gateway --set-file backendConfig=config/backends.yaml
helm template wes-gateway charts/wes-gateway --set-file backendConfig=config/backends.yaml
skaffold diagnose --yaml-only
```
