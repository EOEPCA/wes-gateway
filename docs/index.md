# WES API Gateway

WES API Gateway exposes the GA4GH Workflow Execution Service API as the HTTP contract for submitting, observing, and cancelling workflow runs. In this project, the gateway is the API boundary in front of a Toil workflow execution layer, so clients can use standard WES calls while Toil performs the workflow execution work.

The source currently defines a FastAPI service generated from the WES OpenAPI schema:

- `src/wes_api_gateway/main.py` declares the WES endpoints.
- `src/wes_api_gateway/models.py` declares the request and response models.
- `schemas/openapi.json` is the bundled GA4GH WES OpenAPI contract used to generate the API surface.
- `docs/c4/components/OpenAPI/apidoc.html` is the generated OpenAPI reference.

The documentation is organised with the [Diataxis](https://diataxis.fr/) convention:

- **Tutorials** help you learn the API by completing a small workflow run.
- **How-to guides** show task-focused procedures such as submitting, monitoring, and cancelling runs.
- **Reference** lists endpoints, fields, states, and generated OpenAPI material.
- **Explanation** describes how this gateway relates to Toil and why the API is structured this way.

## API Shape

The public API follows the WES base path used by Toil and the OpenAPI schema:

```text
/ga4gh/wes/v1
```

For local experiments, a Toil WES service commonly listens at:

```text
http://localhost:8080/ga4gh/wes/v1
```

Use `GET /service-info` to discover the workflow languages, WES versions, filesystem protocols, engine versions, default engine parameters, service metadata, and state counts exposed by a deployment.

## Where To Start

If you are new to the gateway, start with [Submit and monitor a CWL workflow](tutorials/submit-and-monitor-cwl.md).

If you already know WES and need a command, use the how-to guides:

- [Submit workflow runs](how-to-guides/submit-workflow-runs.md)
- [Monitor and cancel runs](how-to-guides/monitor-and-cancel-runs.md)

For the exact API contract, see [API reference](reference/api.md) and the [generated OpenAPI page](c4/components/OpenAPI/apidoc.html).
