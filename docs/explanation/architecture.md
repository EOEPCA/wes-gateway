# Gateway and execution backends

The gateway provides a common HTTP entry point for workflow submission and
monitoring. Execution remains the responsibility of each registered WES backend.
This separation lets an installation expose several execution environments without
requiring workflow users to know their internal service addresses.

## C4 architecture model

The [C4 model pages](c4/index.md) explain the architecture at different levels:

- [System context](c4/system-context.md): users, operators and external execution systems.
- [Gateway containers](c4/containers.md): the API and persistent run metadata.
- [WES request flow](c4/request-flow.md): submission, monitoring, cancellation and listing.

The [target hybrid architecture](c4/target-hybrid.md) explains the original
proposal and the capabilities still planned beyond this implementation.

## Deployment boundaries

The [Kubernetes deployment view](c4/deployment.md) shows all nine bundled Helm
releases, internal service connections, and tenant-specific and shared storage.
The gateway and Toil remain separate services even when Skaffold installs them
together. Registering a backend connects an existing WES service; it does not
provision its execution infrastructure.

## Logical namespaces and routing

A logical namespace in `/wes/v1/{namespace}` selects a backend through the
registry. Its name need not match a Kubernetes namespace. Multiple logical
namespaces can share one backend, or each can select a separate deployment.

A submitted run belongs to the logical namespace used at submission. Listing and
retrieving runs respects that association. Namespace routing does not provide
caller authentication or separate execution queues. The deployment's external
access layer must enforce who may use each namespace. The selected target uses
an external API gateway for OIDC token validation and enforcement, with a policy
engine such as OPA. These responsibilities are outside the WES Gateway
implementation. See [identity and run ownership](c4/target-hybrid.md#identity-and-run-ownership)
for the access boundary and the unresolved per-run ownership requirement.

## Run identity and persistence

The [request-flow diagram](c4/request-flow.md) follows submission and subsequent
requests through the gateway, metadata store and selected backend.

The gateway records a submission before forwarding it and returns its own run ID.
Later requests use that ID to find the original backend run. Consequently, a
namespace's listing contains runs recorded in the gateway's database; it does not
include workflows submitted directly to Toil.

Changing a namespace's backend mapping affects future submissions. Existing runs
still use their recorded backend, so that backend's identity and address must
remain available. Removing a logical namespace makes its run routes inaccessible.

The database is therefore part of the installation's durable state. SQLite on a
persistent volume supports a single gateway replica. PostgreSQL supports shared
metadata across replicas. Losing the database loses the associations required to
access runs through the gateway, even if the backend still holds those runs.

## Submission uncertainty and cancellation

A connection can fail after the backend accepts a workflow but before the gateway
receives its run ID. Repeating the submission could start a second workflow.
The gateway keeps the uncertain record, exposes `UNKNOWN`, and uses reserved tags
to support [reconciliation](../how-to-guides/configure-backends.md#reconcile-an-uncertain-submission).
It does not automatically retry submission or cancellation.

Cancellation is asynchronous. An accepted cancellation request can leave a run
in `CANCELING` while the backend stops execution. Only a subsequent backend state
confirms that the run reached `CANCELED`.

## Backend capabilities and artifacts

Each namespace's `/service-info` describes its backend's supported WES and workflow
versions. Registering a service does not add workflow types or task endpoints that
it lacks. The gateway returns the backend's states and supported response data.

Supported HTTP logs and explicitly configured S3 outputs are exposed through
stored gateway artifact URLs associated with the run. Other output locations
remain metadata. This allows clients to retrieve supported artifacts through the
gateway while workflow storage remains with the backend.

For deployment steps, see [Deploy with Toil WES](../how-to-guides/deploy-with-toil.md).
For exact settings and route behavior, use the [configuration](../reference/configuration.md)
and [API](../reference/api.md) references.

## Extending execution to HPC

An HPC cluster can be connected through an independently configured, compatible
WES service. The existing registry and namespace routes provide the gateway side
of that connection. Follow [Add an HPC-backed WES service](../how-to-guides/add-hpc-backend.md)
for registration, credentials and verification.

This supports the proposal's common WES interface and explicit backend selection.
It does not provide scheduler provisioning, automatic cloud/HPC selection, data
staging, or evidence of successful execution on an HPC facility. Those activities
remain part of the [target hybrid architecture](c4/target-hybrid.md).
