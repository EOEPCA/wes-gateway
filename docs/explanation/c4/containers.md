# Gateway containers

This C4 level 2 view shows the gateway API and the persistent data it needs to serve workflow users.

![C4 container view: gateway API and persistent run metadata](../../diagrams/out/containers.svg)

The API serves requests and uses the metadata store to retain run ownership.
In C4 terminology, a container is an application or data store: SQLite is embedded
in the gateway process and stored on a PVC, not a separate database server.
PostgreSQL can replace it when shared metadata is needed across gateway replicas.
The registry is mounted configuration rather than a separate running service.

## Why metadata matters

The API returns a gateway run ID and uses its metadata to find the corresponding
backend run. A status or cancellation request therefore requires both a reachable
backend and the original gateway metadata. Losing that metadata breaks the
association even if Toil still holds the workflow.

The API loads namespace mappings and backend settings from the registry at startup.
The registry describes where new submissions go; the database remembers where
existing runs were submitted. These are separate responsibilities.

Logs and supported output files are streamed through the API using recorded
artifact references. S3 retrieval requires explicit configuration and credentials;
the gateway does not own the backend's workflow storage.

Continue with [Kubernetes deployment](deployment.md) to see where these elements
run, or return to the [C4 model overview](index.md).
