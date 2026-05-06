# Submit Workflow Runs

Use `POST /runs` to create a workflow run. The request is `multipart/form-data` so the gateway can receive both WES metadata fields and optional workflow files.

## Discover Supported Values

Before submitting, check what the deployment supports:

```sh
curl "$WES_URL/service-info"
```

Look at these fields:

- `workflow_type_versions`: accepted workflow languages and versions, such as CWL or WDL.
- `workflow_engine_versions`: workflow engines exposed by the deployment. For this gateway, execution is backed by Toil.
- `default_workflow_engine_parameters`: Toil or deployment defaults that are applied when a run starts.
- `supported_filesystem_protocols`: URL schemes the service can read or write.

## Submit an Attached CWL Workflow

Use an attached workflow when the workflow file is local to the client:

```sh
curl --location --request POST "$WES_URL/runs" \
  --user "$WES_AUTH" \
  --form 'workflow_url=workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={"message":"hello"}' \
  --form 'workflow_attachment=@workflow.cwl'
```

`workflow_url` points to the primary workflow. When the workflow is attached in the same request, `workflow_url` can be a relative path matching the uploaded filename.

## Submit a Workflow by URL

Use an absolute URL when the gateway and Toil runner can fetch the workflow directly:

```sh
curl --location --request POST "$WES_URL/runs" \
  --user "$WES_AUTH" \
  --form 'workflow_url=https://example.org/workflows/workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={"input_file":"s3://bucket/input.dat"}'
```

The referenced workflow and input URLs must use protocols supported by the deployment.

## Upload Multiple Files

Repeat `workflow_attachment` for secondary workflow files, tools, or input files:

```sh
curl --location --request POST "$WES_URL/runs" \
  --user "$WES_AUTH" \
  --form 'workflow_url=workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={"reads":"inputs/sample.fastq"}' \
  --form 'workflow_attachment=@workflow.cwl' \
  --form 'workflow_attachment=@sample.fastq;filename=inputs/sample.fastq'
```

Attachment filenames may include subdirectories. They must not include parent-directory traversal such as `..`.

## Pass Toil Engine Parameters

Use `workflow_engine_parameters` for Toil-specific options accepted by the deployment:

```sh
curl --location --request POST "$WES_URL/runs" \
  --user "$WES_AUTH" \
  --form 'workflow_url=workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={"message":"hello"}' \
  --form 'workflow_engine=toil' \
  --form 'workflow_engine_parameters={"--logLevel":"INFO","--workDir":"/tmp/toil"}' \
  --form 'workflow_attachment=@workflow.cwl'
```

Only pass options that the service is configured to allow. A deployment may reject unsupported or unsafe engine parameters.

## Add Tags

Tags are useful for tracing and filtering runs:

```sh
curl --location --request POST "$WES_URL/runs" \
  --user "$WES_AUTH" \
  --form 'workflow_url=workflow.cwl' \
  --form 'workflow_type=CWL' \
  --form 'workflow_type_version=v1.0' \
  --form 'workflow_params={}' \
  --form 'tags={"project":"demo","owner":"eoepca"}' \
  --form 'workflow_attachment=@workflow.cwl'
```

The response body contains `run_id`. Store it with your client-side job metadata so you can monitor or cancel the run later.
