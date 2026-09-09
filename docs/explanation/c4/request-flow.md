# WES request flow

This sequence diagram complements the C4 views by showing how the gateway uses its registry, metadata and selected backend.

[![Namespaced submission, run access and listing](../../diagrams/out/sequence.svg)](../../diagrams/out/sequence.svg)

Open the diagram to view it at full size.

## Submission

The gateway resolves the logical namespace and validates the multipart request.
An unknown namespace returns `404` before any backend request is sent. For a valid
submission, the gateway stores a durable record, forwards the workflow with
reserved association tags, and records the returned backend run ID. The client
receives the gateway run ID.

If the backend accepts the request but its response is lost, the gateway retains
an uncertain submission. Repeating the POST may create another workflow, so
[reconciliation](../../how-to-guides/configure-backends.md#reconcile-an-uncertain-submission)
is used to recover the association.

## Status, details and cancellation

Each run request resolves the gateway ID inside its original logical namespace.
A run requested through another namespace returns `404`. Accepted requests go to
the run's original backend, even if the namespace now routes new submissions to
a different backend.

Run details include available logs and outputs. Supported artifact references
become gateway URLs. Cancellation is asynchronous: a successful POST acknowledges
the request, while subsequent status requests reveal whether it reached `CANCELED`.

## Listing

The gateway pages through its namespace-owned metadata and refreshes known backend
run states. The result contains `workflows` and a namespace-specific pagination
token. Runs submitted directly to Toil are absent from this listing.


For exact routes, fields and error responses, see the [API reference](../../reference/api.md).
Return to the [C4 model overview](index.md).
