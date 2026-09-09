# System context

This C4 level 1 view shows who uses the gateway and which systems it connects to.

![C4 system context: workflow users, operators, gateway and external WES services](../../diagrams/out/context.svg)

The gateway is the system of interest. Toil and other WES implementations remain
external execution systems even when Skaffold installs them in the same cluster.
Operators manage backend registrations; workflow users interact with namespaced
WES routes. Optional backends in this view are extension points, not services
installed by the default deployment.

## Responsibilities

| Participant | Responsibility |
| --- | --- |
| Workflow user | Submits workflows and retrieves run status, logs and outputs |
| Deployment operator | Registers backends and manages configuration, credentials and storage |
| WES Gateway | Provides namespaced routes and retains run ownership |
| Toil or another WES backend | Executes workflows and reports their state and results |
| Artifact storage | Holds backend-managed logs and workflow outputs |

A common gateway endpoint does not imply common execution capabilities. Each
namespace exposes the capabilities of its selected backend. Authentication and
identity-based namespace authorization require an external access layer in the
current deployment. The [target architecture](target-hybrid.md#identity-and-run-ownership)
places token validation and policy enforcement in an external API gateway, with
a policy engine such as OPA. This integration is not included in the bundled stack
and is outside the WES Gateway implementation.

Continue with [Gateway containers](containers.md) to see the gateway's applications
and data stores, or return to the [C4 model overview](index.md).
