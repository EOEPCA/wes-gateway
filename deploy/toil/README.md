# Bundled Toil deployment

This directory contains the values for the Toil services installed by the root
`skaffold.yaml`. Local chart sources are in `charts/toil-bootstrap` and
`charts/toil-wes`, including the runtime patches used by WES and Celery.

Copied from the working tree of `fbrito/toil-bootstrap` at base commit
`46b72b9459a6b62d5a7146085bb7ae6b8e814314`. The source had local changes to tenant
RabbitMQ credentials, broker definitions, and deployment values; those working-tree
versions are included. No files from that checkout are needed at deployment time.

The values and chart contents are copied unchanged. The root Skaffold configuration
adjusts local paths and adds the gateway release and its port forward. SeaweedFS
4.46.0 and RabbitMQ 2.3.8 remain remote, version-pinned Helm dependencies.

For deployment instructions, see
[Deploy the complete stack with Skaffold](../../docs/how-to-guides/deploy-stack-with-skaffold.md).
