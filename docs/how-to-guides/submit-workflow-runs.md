# Submit Workflow Runs

Use `POST /runs` to create a workflow run. The request is `multipart/form-data` so the gateway can receive both WES metadata fields and optional workflow files.

Run commands from the repository root. Each submission example creates a new run;
choose the one appropriate to your workflow. Set the namespace explicitly:

```sh
export WES_URL=http://localhost:8090/wes/v1/tenant-a
```

For commands using bundled files and expected results, follow the
[curl tutorial](../tutorials/submit-and-monitor-cwl.md). The generic filenames and
`example.org` URL below are placeholders to replace with your own workflow inputs.

## Discover Supported Values

Before submitting, check what the deployment supports:

```sh
curl --fail-with-body -sS --max-time 60 "$WES_URL/service-info"
```

Look at these fields:

- `workflow_type_versions`: accepted workflow languages and versions, such as CWL or WDL.
- `workflow_engine_versions`: workflow engines exposed by the deployment. For this gateway, execution is backed by Toil.
- `default_workflow_engine_parameters`: Toil or deployment defaults that are applied when a run starts.
- `supported_filesystem_protocols`: URL schemes the service can read or write.

## Submit an Attached CWL Workflow

Use an attached workflow when the workflow file is local to the client:

```sh
curl --fail-with-body -sS --max-time 60 --request POST "$WES_URL/runs" \
  --form 'workflow_url=workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={"message":"hello"}' \
  --form 'workflow_attachment=@workflow.cwl'
```

`workflow_url` points to the primary workflow. When the workflow is attached in the same request, `workflow_url` can be a relative path matching the uploaded filename.

## Submit a Workflow by URL

Use an absolute URL when the Toil runner can fetch the workflow directly:

```sh
curl --fail-with-body -sS --max-time 60 --request POST "$WES_URL/runs" \
  --form 'workflow_url=https://example.org/workflows/workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={"input_file":"s3://bucket/input.dat"}'
```

The referenced workflow and input URLs must use protocols supported by the deployment.

## Upload Multiple Files

Repeat `workflow_attachment` for secondary workflow files, tools, or input files:

```sh
curl --fail-with-body -sS --max-time 60 --request POST "$WES_URL/runs" \
  --form 'workflow_url=workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={"reads":"inputs/sample.fastq"}' \
  --form 'workflow_attachment=@workflow.cwl' \
  --form 'workflow_attachment=@sample.fastq;filename=inputs/sample.fastq'
```

Attachment filenames may include subdirectories. The gateway rejects empty, absolute, backslash-containing or parent-traversing
filenames, and duplicate attachment names.

## Pass Toil Engine Parameters

Use `workflow_engine_parameters` for Toil-specific options accepted by the deployment:

```sh
curl --fail-with-body -sS --max-time 60 --request POST "$WES_URL/runs" \
  --form 'workflow_url=workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={"message":"hello"}' \
  --form 'workflow_engine=toil' \
  --form 'workflow_engine_parameters={"--logLevel":"INFO"}' \
  --form 'workflow_attachment=@workflow.cwl'
```

The gateway validates the parameter object and forwards it to the backend. It does
not implement an engine-option allowlist. Use parameters supported by the selected
backend; avoid overriding its configured work directory or storage options unless
your deployment explicitly supports doing so.

## Add Tags

Tags provide metadata for tracing runs; the gateway does not provide a tag-filter
query on `GET /runs`. Reserved `gateway.namespace`, `gateway.backend`, and
`gateway.run_id` values are assigned by the gateway.

```sh
curl --fail-with-body -sS --max-time 60 --request POST "$WES_URL/runs" \
  --form 'workflow_url=workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={}' \
  --form 'tags={"project":"demo","owner":"eoepca"}' \
  --form 'workflow_attachment=@workflow.cwl'
```

The response body contains `run_id`. Store it with your client-side job metadata so you can monitor or cancel the run later.

`workflow_params` is required, even when its value is `{}`. JSON objects in tags
and engine parameters must map strings to strings. A `workflow_engine_version`
requires `workflow_engine`. Do not automatically retry submission after a timeout;
use [run recovery](configure-backends.md#namespace-ownership-and-run-recovery).
