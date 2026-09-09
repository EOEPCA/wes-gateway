# WES Gateway

EOEPCA's WES Gateway gives workflow users a namespaced HTTP endpoint for Toil WES
and other registered WES services. It forwards workflow submissions and retains
the associations needed to retrieve status, logs, outputs, and cancel runs.

The deployment uses a Helm chart, a declarative backend registry, and persistent
run metadata. Deploy the complete stack from this repository with
`skaffold run --port-forward`, or use Helm to connect the gateway to an existing
Toil service. Clients use `/wes/v1/{namespace}`.

Follow [Deploy the complete stack with Skaffold](docs/how-to-guides/deploy-stack-with-skaffold.md)
for prerequisites, configuration, and cleanup behavior.

## Documentation

- **Tutorial:** [Run your first workflow with curl](docs/tutorials/submit-and-monitor-cwl.md).
- **How-to guides:** [Deploy with Toil WES](docs/how-to-guides/deploy-with-toil.md),
  [add additional backends](docs/how-to-guides/add-backends.md),
  [configure storage and credentials](docs/how-to-guides/configure-backends.md),
  [submit workflows](docs/how-to-guides/submit-workflow-runs.md),
  [monitor and cancel runs](docs/how-to-guides/monitor-and-cancel-runs.md), and
  [troubleshoot](docs/how-to-guides/troubleshoot.md).
- **Reference:** [Configuration settings](docs/reference/configuration.md) and
  [API routes and errors](docs/reference/api.md).
- **Explanation:** [Gateway and execution backends](docs/explanation/architecture.md),
  including the deployment diagram, namespace routing, and persistent run ownership.

The running gateway also provides interactive API documentation at `/docs` and
its API description at `/openapi.json`.
