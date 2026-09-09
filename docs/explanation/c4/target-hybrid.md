# Target hybrid architecture

This page describes the intended architecture in the original Processing Building
Block proposal, refined to place authentication and authorization in an external
API gateway and policy layer. It is a target view, not a deployment guide or a statement that
these capabilities are available. The [current deployment](deployment.md) shows
what the bundled configuration installs.

[![Proposed hybrid execution architecture, with planned capabilities labelled](../../diagrams/out/target-hybrid.svg)](../../diagrams/out/target-hybrid.svg)

Open the diagram to view it at full size. Relationships involving planned services
express intended responsibilities; they do not define an implemented protocol or
final deployment topology.

## Common execution interface

The proposal uses WES to separate workflow submission and monitoring from the
execution environment. Independent Toil WES deployments connect to Kubernetes or
to HPC schedulers such as SLURM and PBS Pro. The Zoo-Project WES runner and a common
Python WES client are intended to give applications the same interface for both.

The gateway already provides namespaced routing to configured WES services. The
target adds selection based on policy, resource availability, cost or user
preference. The design must define how those policies choose among execution
domains permitted for the requested namespace. A logical namespace would map to
a Kubernetes namespace or an HPC partition/account.

Workflow portability is an objective, not a guarantee established by WES routing.
The selected backend must support the workflow language, runtime, resource needs
and data locations. Cross-backend validation must demonstrate consistent results
for representative workflows, including HPC container environments such as
Apptainer where applicable.

## Identity and run ownership

The original proposal assigned authentication and authorization to a gateway
layer. The selected architecture places that responsibility in an **external API
gateway**, separate from the WES Gateway implementation. The API gateway validates
OIDC-issued JWT access tokens and enforces access decisions from a policy engine
such as OPA. This integration is planned; the bundled Skaffold stack does not
install an API gateway, OIDC provider or OPA policies.

| Responsibility | Owner |
| --- | --- |
| Issue access tokens | Common OIDC identity provider |
| Validate tokens and enforce access decisions | External API gateway |
| Evaluate namespace and operation permissions | External policy engine, for example OPA |
| Resolve namespaces, forward WES requests and retain run associations | WES Gateway |
| Restrict direct access to internal services | Deployment networking and access configuration |

The policy input must use the verified caller identity, logical namespace and
requested operation. Enforcement must cover submission, listing, details, status,
cancellation, task endpoints and artifact retrieval, as well as any enabled legacy
route aliases. Unmatched routes must not provide an alternative access path.
Clients must not be able to bypass the access layer and reach either WES Gateway
or Toil directly. The local port forwards in the bundled deployment provide direct
access and are not an example of this protected topology.

The WES Gateway's namespace-scoped records retain the original backend association;
they do not establish authenticated user ownership. Namespace-level permissions
alone do not fulfil the original proposal's **per-run user ownership** requirement.
If that requirement is retained, the external policy layer needs a trusted mapping
from run ID to submitting user, with a defined capture and lookup mechanism.
User-provided tags are not proof of ownership. Listing and log/output access must
also respect the chosen ownership policy. That integration remains unresolved;
it is not implemented by adding route permissions alone.

OIDC validation and RBAC are therefore outside the WES Gateway implementation
scope, while deployment integration and authorization policy remain required for
an authenticated installation. Backend identity propagation and HPC account
mapping also need a concrete design.

## Execution middleware and data movement

The proposed middleware reconciles cloud orchestration with HPC batch scheduling.
Its responsibilities include resource-descriptor mapping, queue handling, temporary
storage, and input/output staging between EOEPCA data spaces and execution storage.
Monitoring and logging should provide a consistent view across those environments.

The diagram groups these responsibilities conceptually; it does not prescribe a
new standalone service. Their placement among the gateway, Toil, Zoo and supporting
services remains a design decision. The gateway's existing artifact retrieval is
not a data-staging or synchronization service.

## ESA Space HPC integration

The proposal separately calls for Zoo-based submission and monitoring against
ESA's HPC access interfaces, secure credentials compatible with ESA policies, and
automated data transfer with traceability and provenance. The diagram shows this
as a planned integration path. How it joins the generic WES routing path must be
agreed with the ESA HPC administrators; no ESA endpoint or working adapter is
configured in the bundled stack.

Completion requires end-to-end execution on ESA infrastructure, validation of
input/output transfers, and performance benchmarking under representative loads.
The broader Processing Building Block must also retain alignment with OGC API -
Processes and EOAP; this does not mean the gateway itself currently exposes those
interfaces.

## Current implementation and remaining capabilities

| Area | Available in this repository | Target work still required |
| --- | --- | --- |
| Backends | Two Kubernetes Toil tenants; configurable HTTP WES registrations | SLURM/PBS Pro deployment integration and workflow validation |
| Routing | Explicit namespace-to-backend mapping; durable original-backend association | Policy-based selection and execution-domain mapping |
| Authentication and authorization | Namespace-scoped run records; enforcement external to WES Gateway | Integrate an API gateway with OIDC and a policy engine such as OPA; resolve trusted per-run ownership |
| Client access | WES API and curl examples | Zoo-Project runner and common Python client integration |
| Data | Retrieval of supported logs and outputs | Cloud/HPC staging, synchronization and provenance |
| Monitoring | Forwarded backend status, logs and cancellation | Cross-backend consistency and performance metrics validation |
| ESA Space HPC | No configured integration | Approved access interfaces, secure submission, transfers and benchmarking |

For implemented behavior, return to [System context](system-context.md),
[Gateway containers](containers.md), or [WES request flow](request-flow.md).

## Connecting an HPC service with the current gateway

The [HPC backend guide](../../how-to-guides/add-hpc-backend.md) describes the
available registration path: deploy a compatible WES service at the facility,
register its URL and credentials, and map a logical namespace to it. This is an
operational use of the existing HTTP backend interface, not a new scheduler adapter.

| Proposed activity | Contribution of the documented path | Evidence still needed |
| --- | --- | --- |
| Modular cloud/HPC execution | Declarative registration and a common namespaced WES endpoint | A working scheduler-backed WES service and representative workflow results |
| Unified lifecycle and monitoring | Submission, listing, status, detail, logs and cancellation through the gateway | End-to-end verification against the selected HPC backend |
| Portable CWL execution | The same submission interface and example workflow packages | Compatible runtimes, data access, and comparison of results across environments |
| Data staging and synchronization | Explicit description of current artifact retrieval limits | Input/output transfer mechanisms and provenance validation |
| ESA Space HPC integration | A registration mechanism if a compatible endpoint becomes available | ESA-approved access, Zoo integration, execution tests and benchmarking |

Documentation establishes the integration procedure. It does not demonstrate
completion of the planned HPC or ESA deployment and validation activities.
