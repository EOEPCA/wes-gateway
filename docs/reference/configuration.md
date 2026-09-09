# Configuration reference

The Helm chart is `charts/wes-gateway`. The registry maps logical namespaces to
WES backends. For deployment steps, see [Deploy with Toil WES](../how-to-guides/deploy-with-toil.md).

## Registry

`version`, `backends` and `namespaces` are required. Backend and namespace IDs must
contain 1–63 letters, digits, dots, underscores or hyphens, beginning with a letter
or digit. IDs and namespace names are case-sensitive.

| Setting | Default | Meaning |
| --- | --- | --- |
| `version` | Required | Registry format version; must be `1` |
| `backends` | Required | Nonempty mapping from backend IDs to settings |
| `namespaces` | Required | Nonempty mapping from logical names to `{backend: ID}` |
| `default_namespace` | None | Namespace used by optional legacy-path redirects |
| `max_upload_bytes` | 67108864 | Maximum total incoming request size, including multipart framing |

### Backend settings

| Setting | Default | Meaning |
| --- | --- | --- |
| `type` | `toil` | `toil` or `wes`; both communicate using WES over HTTP |
| `base_url` | Required | Full backend API root; HTTP(S), without embedded credentials, query or fragment |
| `connect_timeout` | 10 seconds | Connection timeout, greater than 0 and at most 300 |
| `read_timeout` | 60 seconds | HTTP read/write/pool timeout, greater than 0 and at most 3600 |
| `keepalive_expiry` | 1 second | Idle connection reuse window, 0–300; 0 disables reuse |
| `verify_tls` | true | Verify backend HTTPS certificates |
| `bearer_token_env` | None | Environment variable containing a backend bearer token |
| `s3` | None | Optional settings for retrieving S3 output artifacts |

Toil commonly uses `/ga4gh/wes/v1` as its API root. Use the actual root for another
WES implementation. Client authorization headers are not forwarded automatically.

### S3 artifact settings

These settings belong under a backend's `s3` mapping:

| Setting | Default | Meaning |
| --- | --- | --- |
| `endpoint_url` | None | Optional HTTP(S) S3-compatible endpoint |
| `region` | `us-east-1` | S3 region |
| `access_key_env` | Required | Environment variable holding the access key |
| `secret_key_env` | Required | Environment variable holding the secret key |
| `allowed_prefixes` | Required | Nonempty list of `s3://bucket/prefix/` locations, each ending in `/` |

Only recorded backend output references under an allowed prefix receive gateway
artifact links. Directory listing is limited to 10000 entries. These settings
control gateway retrieval; they do not configure Toil's workflow storage.

### Validation and update behavior

Unknown registry fields, duplicate YAML keys, invalid values, missing namespace
references and missing credential environment variables cause startup failure.
A temporarily unavailable backend does not invalidate the registry.

Configuration is loaded at startup. A Helm upgrade that changes the registry
changes the pod-template checksum and rolls the Deployment. There is no public
registration API or in-process reload. A backend ID already bound to run metadata
cannot be removed or assigned a different type/base URL.

## Helm values

| Value | Default | Meaning |
| --- | --- | --- |
| `image.repository` | `dev.local/eoepca/wes-gateway` | Image repository; replace for direct Helm installation |
| `image.tag` | `latest` | Image tag when `image.ref` is empty |
| `image.ref` | Empty | Complete image reference; overrides repository/tag |
| `image.pullPolicy` | `IfNotPresent` | Image pull policy |
| `imagePullSecrets` | `[]` | Kubernetes pull-Secret references |
| `replicaCount` | 1 | Number of gateway replicas |
| `service.type` | `ClusterIP` | Service type |
| `service.port` | 8090 | Service port; container port remains 8090 |
| `serviceAccount.create` | true | Create a ServiceAccount with token automount disabled |
| `serviceAccount.name` | Empty | Override the account name; defaults to the release-derived name when creating, otherwise `default` |
| `persistence.enabled` | true | Mount metadata storage at `/data` |
| `persistence.size` | `1Gi` | Requested size for a chart-created PVC |
| `persistence.storageClass` | Empty | StorageClass; empty uses the cluster default |
| `persistence.existingClaim` | Empty | Use an externally managed PVC instead of creating one |
| `database.url` | `sqlite:////data/wes-gateway.db` | Database URL when no Secret is configured |
| `database.secretName`, `database.secretKey` | Empty | Set together to obtain the database URL from a Secret |
| `backendConfig` | Empty | Complete registry YAML, commonly supplied with `--set-file` |
| `registry` | Two sample Toil tenants | Registry used only when `backendConfig` is empty |
| `extraEnv` | `[]` | Additional Kubernetes environment entries, including Secret references |
| `resources.requests` | CPU 100m, memory 128Mi | Requested container resources |
| `resources.limits` | Memory 512Mi | Container resource limit |
| `nodeSelector`, `affinity` | `{}` | Pod placement settings |
| `tolerations` | `[]` | Pod tolerations |
| `nameOverride`, `fullnameOverride` | Empty | Resource naming overrides |

`backendConfig` takes precedence over `registry` and replaces it in full. Helm
merges maps and replaces lists when applying values files. `extraEnv` must not
override `WES_BACKENDS_CONFIG` or `WES_DATABASE_URL`.

SQLite requires persistence and one replica. The chart uses ReadWriteOnce and a
Recreate Deployment strategy. A database Secret's contents cannot be checked during
chart rendering; use PostgreSQL if increasing replicas. Chart-created PVCs are
removed on uninstall; externally managed claims are not owned by the release.

## Container environment and probes

| Name or route | Helm default / behavior |
| --- | --- |
| `WES_BACKENDS_CONFIG` | `/app/config/backends.yaml`, mounted from the ConfigMap |
| `WES_DATABASE_URL` | Set from chart database values or the selected Secret |
| `GET /healthz` | Process liveness, response `{"status":"ok"}` |
| `GET /readyz` | Metadata database readiness, response `{"status":"ready"}` |

Probes do not check Toil availability. Use namespaced `/service-info` to check HTTP
connectivity and submit a workflow to check execution.
