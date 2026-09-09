# WES Gateway

The gateway exposes registered WES services under `/wes/v1/{namespace}`. It forwards
workflow execution requests to Toil and stores durable namespace/backend associations
for each gateway run ID. The included registry points to the two `toil-bootstrap`
tenants. Skaffold builds the image and installs the Helm chart in
`charts/wes-gateway`, which creates a Deployment, Service, ConfigMap and metadata PVC.

Start with [deploying the gateway with Toil WES](how-to-guides/deploy-with-toil.md), then
[run a workflow with curl](tutorials/submit-and-monitor-cwl.md).
To extend a running installation, see [Add additional backends](how-to-guides/add-backends.md).
The [API reference](reference/api.md) describes public routes, multipart fields,
namespace pagination, and errors. The running service publishes `/openapi.json`
and `/docs`; the generated upstream HTML is a schema reference only.

A local gateway endpoint is `http://localhost:8090/wes/v1/tenant-a`. Toil's internal
endpoint remains `/ga4gh/wes/v1`. Use namespaced `/service-info` to discover the
backend's actual supported WES and workflow versions.

See the [architecture](explanation/architecture.md) for ownership, persistence,
and recovery. Identity-based authentication/authorization is supplied separately.
