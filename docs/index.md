# WES Gateway

Deploy the gateway to give workflow users a namespaced HTTP endpoint for Toil WES
and other registered WES services. These guides are for people deploying and
operating the gateway and submitting workflows through it.

Choose a section according to what you need:

| Section | Purpose | Start here |
| --- | --- | --- |
| Tutorials | Learn by completing a guided example | [Run your first workflow](tutorials/submit-and-monitor-cwl.md) |
| How-to guides | Accomplish a deployment or operational task | [Deploy with Toil WES](how-to-guides/deploy-with-toil.md) |
| Reference | Look up settings, defaults, routes, and errors | [Configuration](reference/configuration.md) · [API](reference/api.md) |
| Explanation | Understand routing, execution, and persistence | [Gateway and execution backends](explanation/architecture.md) |

For a new installation, [deploy the complete stack with Skaffold](how-to-guides/deploy-stack-with-skaffold.md),
or deploy the gateway with an existing Toil service. Then follow the tutorial to
submit a workflow. For an existing installation, see [Add additional backends](how-to-guides/add-backends.md),
[Configure storage and backend credentials](how-to-guides/configure-backends.md), or
[Troubleshoot deployment and runs](how-to-guides/troubleshoot.md).
