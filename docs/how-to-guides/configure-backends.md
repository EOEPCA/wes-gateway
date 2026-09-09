# Configure storage and backend credentials

Use these procedures to change an installed Helm release. Commands assume release
and namespace `wes-gateway`. Preserve your existing image, registry and values.
Do not run manual upgrades while another deployment tool is managing the release.
For a list of fields and defaults, see [Configuration reference](../reference/configuration.md).

## Use backend credentials

1. Provision a Secret in `wes-gateway` containing the backend's bearer token.
2. Add `bearer_token_env: BACKEND_TOKEN` to that backend's registry entry.
3. Supply the environment variable through Helm values:

```yaml
extraEnv:
  - name: BACKEND_TOKEN
    valueFrom:
      secretKeyRef:
        name: backend-credentials
        key: token
```

Save this in your values file, preserving other `extraEnv` entries. Apply the values
and the complete registry:

```sh
helm upgrade wes-gateway charts/wes-gateway \
  --namespace wes-gateway --reuse-values \
  --values YOUR_VALUES_FILE \
  --set-file backendConfig=YOUR_REGISTRY_FILE \
  --wait --timeout 5m
```

Missing credential variables prevent startup. Keep secret values out of registry
URLs. Backend credentials authenticate the gateway to WES; they do not authenticate
clients to the gateway.

## Keep SQLite metadata across release removal

Provision a ReadWriteOnce PVC in `wes-gateway` outside the Helm release, then set:

```yaml
replicaCount: 1
persistence:
  enabled: true
  existingClaim: gateway-metadata
```

Apply these settings with your complete deployment values. The externally managed
claim survives Helm uninstall. A chart-created PVC does not.

If changing the claim of an existing gateway, stop submissions, back up the
metadata, and migrate it to the new volume before switching claims. Pointing the
gateway at an empty database will not import its old run associations from Toil.
A pod restart using the same database retains those associations.

## Use PostgreSQL for shared metadata

Provision PostgreSQL and a Secret in `wes-gateway` whose key `url` contains the
connection URL in `postgresql+psycopg://...` format. Configure:

```yaml
database:
  secretName: gateway-database
  secretKey: url
persistence:
  enabled: false
replicaCount: 1
```

Apply the values and start one replica first to initialize its database tables.
Then increase `replicaCount` if needed. All replicas must use the same database
and registry. The gateway image includes the PostgreSQL driver.

Changing database URLs does not migrate existing SQLite records. Arrange metadata
migration and backups before switching an installation with existing runs. Verify
that old run IDs still resolve before reopening submissions.

## Enable retrieval of S3 outputs

Under the relevant backend entry in the registry, add:

```yaml
s3:
  endpoint_url: http://seaweedfs-s3.seaweedfs.svc:8333
  region: us-east-1
  access_key_env: ARTIFACT_ACCESS_KEY
  secret_key_env: ARTIFACT_SECRET_KEY
  allowed_prefixes:
    - s3://tenant-a-results/workflows/
```

Replace the endpoint and allowed prefix with your actual output storage. Supply
both credential variables using Secret-backed `extraEnv` entries, as above. Apply
the complete registry and Helm values, then retrieve a completed run and follow
its returned output artifact URLs.

These settings allow the gateway to retrieve backend-reported artifacts. They do
not provision the bucket or change where Toil writes output. Unsupported locations
remain in run metadata without a downloadable gateway link. The gateway cannot
read Toil's local `file://` locations from its own filesystem.

## Reconcile an uncertain submission

A submission timeout can leave the client unsure whether Toil accepted the work.
Keep the error's `gateway_run_id`. Do not automatically submit the same work again.
Stop the relevant submission activity and run reconciliation inside the gateway
container, where the registry, database and credentials are already configured:

```sh
kubectl exec -n wes-gateway deployment/wes-gateway -- \
  python -m wes_api_gateway.reconcile
```

The command searches backend runs for the gateway's reserved run ID and namespace
tags. Exactly one match restores the association. Zero or multiple matches remain
unresolved for operator investigation. It does not submit or cancel work.

Check the recovered run through its original gateway namespace. Unresolved runs
remain `UNKNOWN` and cannot be cancelled through the gateway until their upstream
association has been recovered.
