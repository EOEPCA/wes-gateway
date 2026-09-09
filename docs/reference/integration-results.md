# Integration validation — 2026-09-09

## Helm deployment follow-up

The gateway now deploys with `charts/wes-gateway` and Skaffold’s Helm deployer.
Helm lint, template checks, and Skaffold diagnostics passed. Launching Skaffold
with the existing Docker group (`sg docker`) resolved the earlier socket-access
blocker: the image built, Helm release `wes-gateway` installed, and the Deployment
became ready. The development session forwarded port 8090 and entered watch mode. Readiness
and both tenant service-info endpoints passed. This records the check at that
time; it is not a claim that the process is still running. The six workflow
cases below were run during the earlier local-gateway validation, not rerun as
part of this chart change.

## Earlier local-gateway validation

Validation used the local gateway on port 28090, forwarding to the existing
`toil-docker` Kubernetes context through local port forwards on 28080/28081.
Both Toil Services ran version 9.4.1 and advertised WES 1.0. The gateway process
used persistent SQLite storage. No new gateway image was deployed to Kubernetes.

## Live acceptance results

| Case | Namespace | Gateway run ID | Result |
| --- | --- | --- | --- |
| Standalone Hello World | tenant-a | `a590077d65c44e4ba433e0ae4a308d11` | COMPLETE; expected greeting; stdout/stderr retrieved |
| Standalone Hello World | tenant-b | `fe7ee237de60420da23339ec8464a1df` | COMPLETE; expected greeting; stdout/stderr retrieved |
| Bootstrap scatter fixture | tenant-a | `b0247e4eeafe4e59b4e6fa2f29be03e8` | COMPLETE; three ordered greeting outputs; stdout/stderr retrieved |
| Bootstrap scatter fixture | tenant-b | `9cff28dccfce41c8a41ccbbbd2cd7c9e` | COMPLETE; three ordered greeting outputs; stdout/stderr retrieved |
| Cancel a running sleep workflow | tenant-a | `ea280f1d96a04647be422d96857940e9` | CANCELED after gateway cancellation; logs retrieved |
| Cancel a running sleep workflow | tenant-b | `ab159a846db849be9be4f5d1637900e0` | CANCELED after gateway cancellation; logs retrieved |
| Evaluated water-bodies workflow | — | — | Deferred at user request; fixtures not supplied |

The six passing cases exercised submission, list, detail, status, cancellation,
service info, namespace metadata, and gateway log retrieval. Each also verified
unknown-namespace rejection and that a run cannot be read or cancelled through
the other namespace. Scalar workflow outputs were retrieved in gateway run detail
JSON and compared with expected values. S3 object byte retrieval has local mocked
test coverage; it was not exercised by these scalar-output workflows.

Detailed evidence is saved locally under `output/integration/{namespace}/{case}/`
(submission, statuses, detail, listing, result, and retrieved logs). This directory
is ignored by Git because run data and logs can contain workflow/deployment details.
The standalone Hello World fixture is new; it is not claimed to be the previously
evaluated package. The scatter fixture is copied from bootstrap's existing
`examples/cwl/hello.cwl` and `hello.inputs.json`.

## Local and deployment checks

- Final local verification: **22 passed**, with seven opt-in live tests skipped;
  Ruff checks and formatting passed. Separately, all six hello/scatter/cancellation
  live cases passed.
- Gateway tests cover full multipart payloads, URL-only submission, reserved tags,
  two backends with colliding upstream run IDs, shared-backend namespace isolation,
  namespace-scoped pagination, restart/remapping, configuration errors and secret
  redaction, transport failures with no POST retries, artifact target restrictions,
  S3 streaming/range responses, and recovery after metadata recording failure.
- Restart verification passed against both live tenants: completed run IDs and
  previously issued artifact links remained usable with the persisted database.
  Evidence: `output/integration/restart-verification.json`.
- Existing schema model tests remain passing. Live tests are opt-in and skipped in
  ordinary unit-test runs; water-bodies remains deferred.
- `uv build` successfully built the sdist and wheel with the corrected packaging.
- `kubectl kustomize .` rendered the configuration and deployment resources.
- Kubernetes server dry-run accepted ServiceAccount, ConfigMap, Service, PVC, and
  Deployment in the existing `default` namespace. The actual manifests target
  `wes-gateway`; validating a newly created namespace and its resources in one
  server dry-run does not persist that namespace, so validation used a temporary
  namespace substitution only. No resources were created.
- Initial container build attempts failed with Docker socket permissions. This was
  resolved in the Helm follow-up above by using the account's existing Docker group;
  image build and deployment subsequently passed. The Kustomize manifests used for
  the earlier dry-run have since been replaced by the Helm chart.
- PostgreSQL support is implemented, but no live PostgreSQL/multi-replica deployment
  was available for validation. The SQLite manifests deliberately use one replica.

## Issues discovered during live testing

Toil closed idle keep-alive connections before the HTTP client's original reuse
window. This caused `RemoteProtocolError` during polling. The gateway now exposes
`keepalive_expiry`, defaulting to one second; repeated polling passed afterward.

Toil emits relative log URLs such as `../../../../toil/wes/v1/logs/{id}/stdout`.
The gateway resolves them against the backend run URL and emits opaque gateway
artifact links. Both stdout and stderr were successfully retrieved through those
links. Toil's `--setEnv` defaults and command arguments are redacted in structured
metadata; raw backend logs are forwarded as produced by Toil.

The initial rapidly overlapping scatter submissions encountered a SeaweedFS
`UploadPart` InternalError. Both scatter cases passed when the fixed test harness
ran workflows sequentially. No SeaweedFS configuration or data was changed.

Cancelling immediately while QUEUED left two initial test runs in backend
`CANCELING`; the gateway correctly preserved that state. Cancelling after RUNNING
reached CANCELED in both tenants. Queued-cancellation completion remains a Toil
backend follow-up, not a state that the gateway fabricates as successful.
