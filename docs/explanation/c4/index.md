# C4 architecture model

These views explain the implemented gateway from its users and external systems
down to the Kubernetes deployment. Start with the system context and follow the
views in order, or choose the question relevant to your installation.

| View | Question it answers |
| --- | --- |
| [System context — level 1](system-context.md) | Who uses the gateway, and which systems execute workflows? |
| [Gateway containers — level 2](containers.md) | Which applications and data stores make up the gateway? |
| [Kubernetes deployment](deployment.md) | Where do the gateway, Toil tenants, messaging and storage run? |
| [WES request flow](request-flow.md) | How do submission, monitoring, cancellation and listing use these services? |

The context and container views describe system responsibilities. The deployment
view shows the bundled Skaffold installation; Toil can also be deployed separately.
The request sequence complements the C4 model with runtime behavior.

The [Target hybrid architecture](target-hybrid.md) is a separate planned view
based on the original proposal. It covers OIDC and authorization, policy routing,
HPC execution, data staging and ESA integration; these are not deployed by the
current Skaffold configuration.

A C4 container means an application or data store, not necessarily a Docker
container. Kubernetes namespaces describe deployment placement; logical WES
namespaces describe gateway routing and run ownership.

For the broader explanation, see [Gateway and execution backends](../architecture.md).
To install the system, follow [Deploy the complete stack with Skaffold](../../how-to-guides/deploy-stack-with-skaffold.md)
or [Deploy with an existing Toil service](../../how-to-guides/deploy-with-toil.md).
