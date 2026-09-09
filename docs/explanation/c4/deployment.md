# Kubernetes deployment

This C4 deployment view maps the bundled installation to Kubernetes namespaces, services and storage.

[![Gateway deployment and backend connections](../../diagrams/out/overall.svg)](../../diagrams/out/overall.svg)

Open the deployment diagram to view it at full size.

The gateway Helm release contains the API service, backend configuration, and
access to a metadata database. The bundled Skaffold configuration installs all
nine Helm releases in this diagram: the gateway, four credential bootstrap
releases, two Toil tenants, RabbitMQ, and SeaweedFS. Each tenant has its own WES
and Celery deployments, shared RWX PVC, and namespace-scoped execution permissions.
Bootstrap releases supply namespace-local Secrets; RabbitMQ uses separate tenant
users and virtual hosts. S3 credentials and the SeaweedFS service are shared.

Gateway-to-Toil requests use `toil-wes.tenant-a.svc:8080` and
`toil-wes.tenant-b.svc:8080`, with `/ga4gh/wes/v1` as the backend API root.
Toil uses `rabbitmq.rabbitmq.svc:5672` and `seaweedfs-s3.seaweedfs.svc:8333`.
Port forwards provide workstation access and are not used for these internal
connections. Workflow jobs use backend storage; the WES/Celery PVC is not
automatically mounted into those jobs.

The deployment diagram shows the bundled default: one gateway replica with SQLite.
PostgreSQL, additional backends, and gateway retrieval from S3 are configurable
alternatives; the default registry does not enable S3 artifact retrieval.
OIDC authentication and identity-based namespace authorization are not installed
by this stack. Toil's Kubernetes RBAC governs execution resources, not which
workflow users may access a gateway namespace.

Toil remains independently deployable. Adding a gateway backend registration makes
an existing WES service reachable; it does not provision its execution resources.
See [Deploy the complete stack with Skaffold](../../how-to-guides/deploy-stack-with-skaffold.md)
or [Deploy with an existing Toil WES service](../../how-to-guides/deploy-with-toil.md).

The gateway's readiness check covers its configuration and metadata storage.
A backend can still be unavailable while the gateway is ready. A namespaced
`/service-info` request checks the route to that backend; a completed workflow
also demonstrates that its execution infrastructure works.

## Shared and tenant-specific resources

| Scope | Resources |
| --- | --- |
| Gateway | API service, backend registry and persistent run metadata |
| Each Toil tenant | WES, Celery worker, workflow jobs, shared WES/Celery PVC and execution RBAC |
| Shared messaging | RabbitMQ with separate tenant users and virtual hosts |
| Shared workflow storage | SeaweedFS with shared S3 credentials |

Sharing the cluster and S3 service does not provide an authorization boundary for
untrusted tenants. Logical namespaces scope gateway run records; they do not
replace the deployment's access controls.

Continue with [WES request flow](request-flow.md) to follow a run through the
services, or return to the [C4 model overview](index.md).
