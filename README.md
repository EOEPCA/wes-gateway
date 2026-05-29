# wes-gateway

`wes-gateway` is the EOEPCA+ Processing Building Block gateway component for
exposing multiple Workflow Execution Service (WES) backends through a single,
consistent API entrypoint.

## Context

The EOEPCA+ Processing Building Block proposes a hybrid execution architecture
where independent WES deployments run on different infrastructures:

- Kubernetes-backed environments
- HPC-backed environments

This repository bootstraps the gateway layer that sits in front of those
backends and provides shared authentication, authorization, and routing
semantics.

## WES API context (GA4GH)

The gateway targets the GA4GH Workflow Execution Service (WES) API, which
defines a standard, platform-agnostic interface to submit and monitor workflows
across different execution backends.

Reference specification:

- GA4GH WES schemas repository:
  `https://github.com/ga4gh/workflow-execution-service-schemas`
- Published API docs (currently showing WES 1.1.0):
  `https://ga4gh.github.io/workflow-execution-service-schemas/docs/`

Core WES endpoint groups include:

- `GET /service-info` for service metadata/capabilities
- `GET /runs` to list workflow runs
- `POST /runs` to submit a workflow run
- `GET /runs/{run_id}` for run logs/details
- `GET /runs/{run_id}/status` for lightweight run state
- `POST /runs/{run_id}/cancel` to request cancellation

WES request/response contracts are defined by GA4GH OpenAPI schemas. For
workflow submission, `POST /runs` uses `multipart/form-data` and commonly
includes fields such as `workflow_url`, `workflow_type`,
`workflow_type_version`, `workflow_params`, and `workflow_attachment`.

In `wes-gateway`, these GA4GH endpoints are exposed through namespace-aware
paths (for example `/wes/v1/{namespace}/runs`) while preserving WES semantics
and forwarding to the correct backend implementation.

## What the gateway provides

- A single entrypoint for WES API access
- OIDC/JWT authentication validation
- Namespace-aware routing to backend WES instances
- Backend abstraction across Kubernetes and HPC execution environments
- Consistent AuthN/AuthZ behavior across infrastructures

## Architecture summary

The gateway is designed to:

- Validate JWT tokens at the gateway layer
- Enforce namespace-level RBAC policies
- Route requests using logical namespace paths such as
  `/wes/v1/{namespace}/runs`
- Map logical namespaces to infrastructure-specific targets:
  - Kubernetes namespaces
  - HPC partitions/accounts

In this model, Toil WES (or other WES-compatible) deployments remain
independent, while `wes-gateway` centralizes access control and request routing.

## Repository status

This repository is currently being bootstrapped to establish the baseline
gateway component within the EOEPCA organization.
