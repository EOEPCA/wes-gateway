# Troubleshoot deployment, routing and failed runs

Use this guide when a deployed gateway or a submitted workflow is not behaving as
expected. Commands assume Helm release and namespace `wes-gateway`, Toil in
`tenant-a`, and kubectl access to the cluster. For HTTP checks, keep a gateway
port forward active and set:

```sh
export WES_URL=http://localhost:8090/wes/v1/tenant-a
```

## Gateway does not start or become ready

```sh
kubectl get pods,pvc -n wes-gateway
kubectl describe deployment wes-gateway -n wes-gateway
kubectl get events -n wes-gateway --sort-by=.metadata.creationTimestamp
kubectl logs -n wes-gateway deployment/wes-gateway --tail=100
```

| Symptom | Check and correction |
| --- | --- |
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

## Namespace or run routing fails

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
one-second default avoids reusing connections after a backend closes them. Reduce
it if your backend closes idle connections sooner.

## Submission or workflow execution fails

A failed HTTP submission and a successfully submitted run in `EXECUTOR_ERROR` are
different failures. Keep the HTTP response and gateway run ID before investigating.

- HTTP 400: check required WES form fields, JSON object values, CWL version, and
  attachment names. `workflow_params=<inputs.json` sends JSON as a text field;
  `workflow_attachment=@workflow.cwl` uploads the workflow file.
- Submission timeout or `gateway_run_id` with unknown outcome: do not resubmit
  automatically. Toil may already have accepted the work. Follow
  [run recovery](configure-backends.md#reconcile-an-uncertain-submission).
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
arguments and workflow data. For a SeaweedFS `UploadPart` InternalError, inspect storage service logs, capacity
and connectivity. Reducing concurrent submissions may help isolate load-related
failures. Gateway routing can work while backend workflow storage is failing.

## Logs or outputs cannot be retrieved

Use log URLs from the gateway run-detail response. A `404` artifact response can
mean the token belongs to a different run/namespace/database. An upstream retrieval
error can mean the artifact is unavailable or removed. S3 File/Directory output
retrieval needs explicit allowed prefixes and credentials; unsupported locations
remain metadata. See [logs and output files](configure-backends.md#enable-retrieval-of-s3-outputs).

## Cancellation stays in CANCELING

Cancellation is asynchronous. Poll until `CANCELED` or another terminal state;
`CANCELING` is not proof of completion. If cancellation remains at `CANCELING`, check the Toil state and worker logs,
including whether the run was queued when cancellation was requested. The gateway
reports the backend state and cannot guarantee that the backend completes cancellation.
