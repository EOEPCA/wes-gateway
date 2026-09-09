# Gateway and execution backends

The gateway provides a common HTTP entry point for workflow submission and
monitoring. Execution remains the responsibility of each registered WES backend.
This separation lets an installation expose several execution environments without
requiring workflow users to know their internal service addresses.

## Deployment boundaries

![Gateway deployment and backend connections](../diagrams/out/overall.svg)

The gateway Helm release contains the API service, backend configuration, and
access to a metadata database. Toil is a separate deployment with its own workers,
Kubernetes jobs, and workflow storage. Adding a gateway backend registration makes
an existing WES service reachable; it does not provision its execution resources.

The gateway's readiness check covers its configuration and metadata storage.
A backend can still be unavailable while the gateway is ready. A namespaced
`/service-info` request checks the route to that backend; a completed workflow
also demonstrates that its execution infrastructure works.

## Logical namespaces and routing

A logical namespace in `/wes/v1/{namespace}` selects a backend through the
registry. Its name need not match a Kubernetes namespace. Multiple logical
namespaces can share one backend, or each can select a separate deployment.

A submitted run belongs to the logical namespace used at submission. Listing and
retrieving runs respects that association. Namespace routing does not provide
caller authentication or separate execution queues. The deployment's external
access layer must enforce who may use each namespace.

## Run identity and persistence

![Submission and namespace ownership](../diagrams/out/sequence.svg)

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
