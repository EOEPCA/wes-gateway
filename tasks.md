# Toil WES integration task breakdown

## Helm deployment update

Kustomize and the raw deployment manifest have been replaced by the Helm chart
in `charts/wes-gateway`. Skaffold builds the Docker image and deploys that chart,
passing `config/backends.yaml` as the complete registry. Helm lint and rendering
checks passed. Skaffold built the container and installed Helm release
`wes-gateway` successfully; at validation time the Deployment was ready and
development mode entered watch mode with port forwarding on 8090. The earlier Docker access
blocker was resolved by launching with the existing docker group via `sg docker`.

## Implementation status — 2026-09-09

Registry, HTTP forwarding, namespace ownership, durable run IDs, recovery, artifact
routes, deployment manifests, examples, and automated tests are implemented.
Validation: 22 local tests and six live workflow cases passed, plus restart/log-link
persistence checks. Ruff and package build passed.
See [integration results](docs/reference/integration-results.md) and
[operator documentation](docs/how-to-guides/configure-backends.md).

| Tasks | Status |
| --- | --- |
| T0 | Live Toil version/capabilities, relative logs, tags, tenant execution verified; exact prior evaluated fixtures remain unidentified |
| R1–R3 | Implemented; config file, validation, multiple backends, ConfigMap/Skaffold integration |
| N1–N3 | Implemented; persistent namespace/run ownership, namespace pagination, compatibility redirects and docs |
| I1–I2 | Implemented and tested against both live Toil tenants |
| I3 | HTTP logs and scalar outputs verified live; configured S3 file streaming tested with a mock |
| I4 | Packaging and manifests fixed; wheel/sdist build and server dry-run pass; image build and Helm deployment subsequently passed (see Helm update above) |
| W1 | Bootstrap scatter reused, standalone hello and cancellation fixtures added; water-bodies deferred at user request |
| W2–W3 | Six live cases passed: hello, scatter, running cancellation in both namespaces; water-bodies deferred |
| W4 | Local and opt-in live suites implemented; evidence saved under output/integration; PostgreSQL HA not tested live |

The inspection baseline below is historical. Checkboxes record completed work;
remaining unchecked items include deployment limits and deferred validation.

## Pre-implementation inspection baseline

Reviewed the local `wes-gateway` repository and
`/data/work/git-terradue-com/fbrito/toil-bootstrap`. These findings describe source
configuration; no cluster deployment or workflow execution was performed.

| Area | Existing implementation | Work needed |
| --- | --- | --- |
| Gateway API | `src/wes_api_gateway/main.py` registers unprefixed WES endpoints, all returning `501`. Submission accepts attachments only. | Implement forwarding, complete multipart fields, and namespace routes. |
| Backend configuration | No backend registry or HTTP client dependency in `pyproject.toml`. | Add validated configuration and a reusable WES HTTP client. |
| Toil deployment | Bootstrap defines `tenant-a` and `tenant-b`, each with a `toil-wes` Service on port 8080, separate WES/Celery storage and RabbitMQ vhosts. | Register both backends and verify connectivity from the gateway. |
| Gateway deployment | Knative manifest still contains Argo settings and `mate-api-sa`. Dockerfile references `/pymate/.`, omits project metadata from its copy, and starts `wes-gateway.main:app`. | Fix packaging, module entrypoint, service account, and registry mounting. |
| Workflow fixtures | `examples/cwl/hello.cwl` is a CWL v1.2 scatter over three messages. `examples/pattern-9.0.3.0.cwl` is a CWL v1.0 Landsat NDVI/NDWI workflow. Both submission scripts accept a WES base URL and call `/service-info`. | Identify the exact evaluated fixtures, provide accessible inputs, and add output assertions. |
| Water-bodies fixture | No explicitly identified water-bodies workflow or evaluation record found in the inspected repository. | Obtain the evaluated package and inputs; do not assume the NDVI/NDWI example is the requested workflow. |
| Validation | Gateway tests check models and route/schema contracts. Bootstrap README says the current two-tenant configuration has not been deployed/tested. | Add forwarding tests and collect live integration evidence. |

Source references: gateway `main.py`, `models.py`, `tests/test_app_contract.py`,
`Dockerfile`, `k8s/knative-service.yaml`, and `Taskfile.yaml`; bootstrap `README.md`,
`config/toil-wes.yaml`, `toil-wes/templates/service.yaml`, `toil-wes/values.yaml`,
and `examples/`.

## Delivery order

1. **T0** — establish backend and workflow baselines.
2. **R1–R3** — implement declarative registration.
3. **N1–N3 and I1–I3** — implement namespace routing, run association, and forwarding.
4. **I4** — deploy the gateway alongside Toil.
5. **W1–W4** — execute workflows and collect acceptance evidence.

Fixture preparation in W1 can start while gateway implementation is underway.
Each task below includes its completion evidence. Task ownership is expressed by
repository; bootstrap changes are planned here, not applied to that checkout.

## T0 — Establish the integration baseline

- [ ] Verify the actual deployed Toil image/version, tenant namespaces, Service endpoints, `/service-info`, shared RWX storage, Celery/RabbitMQ connectivity, S3 access, and image pull requirements. Record configuration revisions and distinguish live checks from rendered manifests.
- [x] Capture representative Toil submission, list, detail, status, cancellation, and error responses. Check compatibility with the gateway's generated WES 1.1.0 models, including required list tags and service metadata.
- [x] Record actual stdout/stderr URLs, task-log support, output locations, and whether Toil preserves request tags. These determine response adaptation and durable namespace metadata design.
- [ ] Identify exact evaluated Hello World, water-bodies, and scatter package revisions, inputs, expected results, and prior direct-Toil evidence. Record unavailable fixtures as explicit blockers to their execution tasks.

**Done when:** a baseline report contains backend capabilities, response fixtures,
and a workflow/input inventory. Owner: both repositories. No integration success
is inferred from HTTP readiness alone.

## 1. Integrate the existing Toil WES Kubernetes deployment

### I1 — Implement the backend HTTP client

- [x] Add a WES client interface and initial Toil-compatible implementation under `src/wes_api_gateway/`; add its runtime dependency to `pyproject.toml`.
- [x] Manage pooled asynchronous client startup/shutdown; configure connection/read timeouts and TLS verification per backend.
- [x] Join the configured base URL with WES resource paths, preserving `/ga4gh/wes/v1`, query parameters, and encoded run IDs.
- [x] Preserve meaningful upstream status codes and WES error bodies; define gateway errors for unreachable backends, timeouts, and malformed responses. Avoid automatically retrying submission or cancellation after ambiguous failures.
- [x] Keep backend credentials in referenced Secrets/environment variables; explicitly control forwarded headers and redact credentials from diagnostics.

**Done when:** mock-backend tests cover path/query forwarding, successful responses,
upstream errors, timeouts, and absence of duplicate POST attempts. Depends on R1–R2.

### I2 — Implement WES operations and complete submission handling

- [x] Implement namespaced `POST /runs`, `GET /runs`, `GET /runs/{run_id}`, `GET /runs/{run_id}/status`, and `POST /runs/{run_id}/cancel` using the resolved backend.
- [x] Also implement namespaced `GET /service-info`: both existing bootstrap scripts require it before submission.
- [x] Accept and forward `workflow_url`, `workflow_type`, `workflow_type_version`, JSON `workflow_params`, optional tags/engine settings, and repeated `workflow_attachment` parts. Support submissions without attachments when the workflow URL is sufficient.
- [x] Preserve attachment filenames, contents, relative references, and packed workflow fragments such as `pattern-9.0.3.0.cwl#pattern-9`; define upload limits and resource cleanup.
- [x] Preserve run-list pagination and terminal states. Adapt only verified Toil/schema differences so valid upstream responses do not become gateway response-validation failures.
- [x] Define behavior for the existing `/tasks` endpoints based on observed backend support; document unavailable capabilities explicitly.

**Done when:** HTTP-level tests exercise all five required operations plus service
info, including multipart payload fidelity, pagination, and failure responses.
Depends on I1 and N1–N2.

### I3 — Make logs and outputs retrievable through the gateway

- [x] Forward run details with request metadata, state, workflow/task logs, and outputs intact.
- [x] Inspect returned log and artifact references and implement gateway routes/URL rewriting where internal Toil addresses would otherwise escape to clients.
- [x] Define and implement file/directory output retrieval through the gateway where needed, including S3-backed artifacts; distinguish output metadata from successful byte retrieval.
- [x] Restrict retrieval to artifacts belonging to the resolved run/backend; never accept arbitrary client-supplied fetch URLs. Preserve streaming and appropriate response headers for large artifacts.

**Done when:** a client can retrieve available stdout/stderr and representative
output contents using gateway URLs, with wrong-namespace access rejected.
Depends on T0, I2, and N2. This includes artifact access beyond the five core WES
operations if the actual Toil responses require it.

### I4 — Wire and validate Kubernetes deployment

- [x] Fix the gateway Dockerfile to copy/install project metadata and source, remove the stale `/pymate/.` reference, and launch `wes_api_gateway.main:app` on port 8090.
- [x] Replace Argo-specific manifest settings with backend registry configuration; create/reference an appropriate gateway service account and mount configuration/Secret references.
- [x] Update gateway Skaffold manifests and document deployment alongside bootstrap. Document the Knative prerequisite or provide a conventional Deployment/Service option for clusters without Knative.
- [ ] Verify gateway-to-Toil DNS/network connectivity for both tenants, readiness behavior, and configuration rollout. Keep liveness independent of temporary backend outages.
- [ ] Build and start the image, render deployment configuration, then run a live submit/list/detail/status/cancel check. Use a sufficiently long workflow for cancellation and verify eventual `CANCELED`, not merely POST acceptance.

**Done when:** the gateway is deployed, both declarative Toil registrations resolve,
and all required operations have recorded live results. Owner: gateway, with
bootstrap deployment instructions where needed. Depends on R3, N3, and I2–I3.

**Acceptance coverage:** Toil registered (R3/I4); requests forwarded (I1/I2);
all five operations work (I2/I4); existing scripts execute through the gateway
(W2/W3).

## 2. Add logical WES namespace routing

### N1 — Define and implement namespace resolution

- [x] Expose `/wes/v1/{namespace}/runs` and its run subresources, plus `/wes/v1/{namespace}/service-info`.
- [x] Resolve logical namespaces through the validated registry, independently of Kubernetes namespace naming; never construct a backend hostname directly from user input.
- [x] Reject unknown namespaces with a documented `404` WES error before contacting a backend; define validation for malformed namespace values.
- [x] Decide and document compatibility for existing unprefixed endpoints and documented `/ga4gh/wes/v1` paths. Any default-backend alias must be explicitly configured and unambiguous.

**Done when:** routing tests prove tenant A/B select the correct backend and an
unknown namespace causes no upstream request. Depends on R1–R2.

### N2 — Retain run-to-namespace association

- [x] Select and document a durable association mechanism after checking Toil tag persistence. Prefer explicit records containing logical namespace, stable backend ID, upstream run ID, and creation time when backend metadata cannot meet persistence/isolation requirements.
- [x] Store the association on submission and expose the namespace in documented run metadata without allowing client tags to override it.
- [x] Resolve detail/status/cancel/log/output access through that association; handle identical upstream run IDs across backends without collisions.
- [x] Scope listing and pagination to the logical namespace. Define behavior for multiple logical namespaces sharing one backend and for runs submitted directly to Toil before gateway integration.
- [x] Define recovery if Toil accepts a run but association recording fails, and define behavior when a namespace is remapped or its backend is removed. Existing runs must not silently route to a different backend.

**Done when:** namespace association survives gateway restart and multiple replicas;
wrong-namespace requests cannot inspect or cancel another namespace's run; remapping
and submission-recording failures have tests. Depends on T0, R1, and N1.

### N3 — Align API contracts and documentation

- [x] Update route/schema tests and namespace examples in `README.md` and `docs/`; distinguish the gateway prefix from Toil's backend prefix.
- [x] Prevent `Taskfile.yaml` skeleton regeneration from overwriting handwritten routing/client code; document the generation workflow and schema source of truth.
- [x] Document that namespace resolution alone does not implement identity-based authorization. Track OIDC/JWT and namespace RBAC separately unless required by the target environment; the current code does not implement the README's advertised authentication.

**Done when:** generated API documentation and tests reflect implemented paths,
namespace errors, and metadata semantics. Depends on N1–N2 and I2.

**Acceptance coverage:** namespaced routes and backend mapping (N1); invalid
namespace rejection (N1); retained run namespace metadata (N2).

## 3. Execute the evaluated CWL workflows through the gateway

### W1 — Prepare reproducible workflow fixtures

- [x] Reuse `examples/cwl/hello.cwl` and `hello.inputs.json` for the existing smoke/scatter check; verify the three ordered greeting strings including trailing newlines.
- [ ] Obtain or identify the evaluated standalone Hello World fixture if it differs from the bundled scatter example; keep Hello World and scatter as separately reported acceptance cases.
- [ ] Obtain the evaluated water-bodies CWL, pinned package/container revisions, representative input data, and expected output checks. Do not substitute `pattern-9` without confirming equivalence.
- [ ] Prepare runtime-accessible input data and required credentials. `run-pattern-9.sh` passes an `item` Directory description; it does not upload the local acquisition directory.

**Done when:** each of the three required workflows has a reproducible package,
input set, expected result, and prerequisite list. Owner: bootstrap/examples or
versioned gateway integration fixtures. Depends on T0.

### W2 — Reuse submission scripts with gateway endpoints

- [x] Add documented gateway invocations or a wrapper using a configurable gateway base URL and logical namespace. Existing scripts already accept a complete WES URL, so no protocol rewrite is needed.
- [x] Add machine-checkable output assertions and save submission, status, final run detail, and error evidence. Make polling timeout and cleanup/cancellation behavior explicit.
- [x] Keep a separate direct-Toil diagnostic invocation to distinguish workflow/deployment failures from gateway forwarding failures.

Example after gateway deployment, with `GATEWAY_URL` set to its reachable origin:

```sh
TOIL_BOOTSTRAP=/data/work/git-terradue-com/fbrito/toil-bootstrap
"$TOIL_BOOTSTRAP/examples/cwl/run-hello.sh" "$GATEWAY_URL/wes/v1/tenant-a"
"$TOIL_BOOTSTRAP/examples/cwl/run-hello.sh" "$GATEWAY_URL/wes/v1/tenant-b"
```

**Done when:** the existing smoke workflow is submitted and monitored entirely
through the gateway. Depends on I4 and W1 for the relevant fixture.

### W3 — Execute and verify each acceptance workflow

- [ ] Execute Hello World through the gateway; assert `COMPLETE` and expected greeting output.
- [ ] Execute water-bodies through the gateway; assert `COMPLETE` and agreed output content/metadata checks against its evaluated baseline.
- [x] Execute scatter through the gateway; assert `COMPLETE`, expected output cardinality, ordering, and values.
- [ ] For every workflow, retrieve status, run details, available logs, and output contents through the gateway; record run ID, namespace, backend ID, versions, inputs, timestamps, and results.

**Done when:** all three cases have passing evidence, including retrievable logs
and outputs. A missing water-bodies package/input set blocks that case; a passing
hello/scatter run does not complete the full acceptance criteria. Depends on W1–W2
and I3.

### W4 — Add repeatable integration validation

- [x] Add an opt-in live integration suite and operator instructions covering the five required operations, two tenant backends, unknown namespace, wrong-namespace run access, backend outage, and restart persistence.
- [x] Keep mocked HTTP forwarding/configuration tests runnable in normal CI without a Kubernetes cluster; run existing model/contract tests after updating contracts.
- [x] Publish an acceptance matrix linking every criterion to a test or recorded execution; record failures and unavailable prerequisites explicitly.

**Done when:** another developer can reproduce the checks and distinguish local
contract tests from successful live workflow execution. Depends on I4, N2, and W3.

## 4. Implement configurable backend registration

### R1 — Define a versioned registry schema

- [x] Add typed configuration for stable backend ID, adapter type, WES base URL, timeouts, TLS settings, and optional credential references; store logical namespace mappings separately.
- [x] Support multiple backend entries, with no Toil endpoint hardcoded in route handlers.
- [x] Specify startup loading, configuration path, and restart/rollout semantics; dynamic registration and hot reload are not required for this first increment.

Proposed initial configuration (schema to implement):

```yaml
version: 1
backends:
  toil-a:
    type: toil
    base_url: http://toil-wes.tenant-a.svc:8080/ga4gh/wes/v1
  toil-b:
    type: toil
    base_url: http://toil-wes.tenant-b.svc:8080/ga4gh/wes/v1
namespaces:
  tenant-a:
    backend: toil-a
  tenant-b:
    backend: toil-b
```

These URLs are derived from bootstrap chart configuration and must be verified
against the deployed Services in T0/I4.

**Done when:** schema and example configuration represent both current tenants
and permit additional registered backend implementations. Owner: gateway.

### R2 — Validate and load the registry

- [x] Validate missing/empty IDs, duplicate keys/IDs, unsupported adapter types, invalid HTTP(S) URLs, invalid timeouts, unknown fields, missing credential references, unsupported schema versions, and namespace references to absent backends.
- [x] Fail startup with actionable field-level messages, including the affected backend/namespace, while redacting secrets.
- [x] Separate invalid configuration from temporary backend unavailability; a down backend must not prevent unrelated healthy namespaces from operating.
- [x] Add positive and negative configuration tests, including two independently routed mock backends.

**Done when:** valid multiple-backend configuration loads and each invalid case
produces a clear diagnostic. Depends on R1.

### R3 — Package declarative Toil registration

- [x] Add a checked-in example registry and Kubernetes ConfigMap mount/configuration-path setting to the existing gateway manifests and Skaffold inputs.
- [x] Document Secret references, adding a backend, assigning a logical namespace, and applying configuration changes. A config file satisfies the acceptance criterion; a new Helm chart is optional.
- [ ] Validate/render the deployment with both Toil entries and confirm startup uses the mounted registry.

**Done when:** operators can configure Toil and a second backend entry without
editing application code. Depends on R1–R2.

**Acceptance coverage:** registry config file (R1/R3); declarative Toil (R3);
multiple backend entries (R1/R2); clear configuration validation errors (R2).
