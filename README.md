# WES Gateway

EOEPCA's WES Gateway exposes registered WES backends through
`/wes/v1/{namespace}`. It forwards workflow submissions to Toil over HTTP and
retains durable namespace/backend associations for monitoring and cancellation.

Implemented endpoints under each namespace:

- `GET /service-info`
- `POST /runs` and `GET /runs`
- `GET /runs/{id}` and `GET /runs/{id}/status`
- `POST /runs/{id}/cancel`
- `GET /runs/{id}/tasks` and `GET /runs/{id}/tasks/{task_id}` (backend support required)
- `GET /runs/{id}/artifacts/{token}` for supported logs and output files

`config/backends.yaml` declaratively registers the `tenant-a` and `tenant-b` Toil
Services from `toil-bootstrap`. Namespace names resolve only through this registry.
Unknown namespaces and wrong-namespace run IDs return `404`.

## Build and deploy

With the separate Toil stack running, execute from this repository root:

```sh
skaffold dev --port-forward
```

Skaffold builds the Docker image and installs the Helm chart in
`charts/wes-gateway`, passing `config/backends.yaml` as the registry. It waits for
the Deployment, forwards port 8090 and watches for changes. Docker, Helm, Skaffold,
and access to the target Kubernetes context are required.

- Gateway namespace URL: `http://localhost:8090/wes/v1/tenant-a`
- Swagger UI: [http://localhost:8090/docs](http://localhost:8090/docs)
- Readiness: `http://localhost:8090/readyz`

For first deployment, follow [Deploy with Toil WES](docs/how-to-guides/deploy-with-toil.md)
for the diagram, Helm examples, registration and troubleshooting.

Start with the [curl tutorial](docs/tutorials/submit-and-monitor-cwl.md) for workflow
submission, results, logs, listing and cancellation. See
[configuration and operations](docs/how-to-guides/configure-backends.md) for
Docker group access, Helm values, persistence, backend Secrets, recovery, and a
separate local Python setup using port-forwarded Toil endpoints.

The default chart uses SQLite on a single-replica PVC. Pod restarts preserve its
records, but Helm uninstall/Skaffold cleanup deletes a chart-created PVC. Configure
an externally managed existing claim when metadata must survive teardown.
Authentication and identity-based namespace authorization are not implemented in
the gateway and must be provided by the deployment's external access layer.

## Execute and verify workflows

For the Python example runner and tests, install the local tools first:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e . pytest
```

```sh
.venv/bin/python examples/run_workflow.py \
  http://localhost:8090/wes/v1/tenant-a \
  examples/cwl/hello.cwl examples/cwl/hello.inputs.json \
  --expected examples/cwl/hello.expected.json --evidence output/hello
```

Use `scatter.cwl`, `scatter.inputs.json`, and `scatter.expected.json` for the
bootstrap's existing three-message scatter workflow. The original bootstrap
`examples/cwl/run-hello.sh` also accepts a gateway namespaced URL unchanged.
The standalone hello fixture here is a new small fixture; it is not claimed to be
an identified prior evaluated package.

```sh
.venv/bin/pytest -q
# Explicitly submits live hello/scatter/cancellation workflows to both tenants:
WES_GATEWAY_URL=http://localhost:8090 .venv/bin/pytest tests/integration -v -s
```

Live evidence is saved under `output/integration/`. The water-bodies case requires
`WES_WATER_BODIES_CWL`, `WES_WATER_BODIES_INPUTS`, and `WES_WATER_BODIES_EXPECTED`;
optional version/entrypoint settings are documented in the integration test.
It is skipped until those evaluated fixtures are available. The bootstrap's
NDVI/NDWI example is not assumed to be the water-bodies workflow.

The generated upstream schema remains in `schemas/openapi.json`. The running
application's `/openapi.json` and `/docs` describe the namespace routes; skeleton
generation writes into `generated/` to preserve handwritten implementation.
