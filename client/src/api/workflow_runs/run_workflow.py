from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.run_id import RunId
from ...models.run_workflow_body import RunWorkflowBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: RunWorkflowBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/runs",
    }

    if not isinstance(body, Unset):
        _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | RunId | None:
    if response.status_code == 200:
        response_200 = RunId.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = ErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | RunId]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RunWorkflowBody | Unset = UNSET,
) -> Response[ErrorResponse | RunId]:
    r"""RunWorkflow

     This endpoint creates a new workflow run and returns a `RunId` to monitor its progress.
    The `workflow_attachment` array may be used to upload files that are required to execute the
    workflow, including the primary workflow, tools imported by the workflow, other files referenced by
    the workflow, or files which are part of the input.  The implementation should stage these files to
    a temporary directory and execute the workflow from there. These parts must have a Content-
    Disposition header with a \"filename\" provided for each part.  Filenames may include
    subdirectories, but must not include references to parent directories with '..' -- implementations
    should guard against maliciously constructed filenames.
    The `workflow_url` is either an absolute URL to a workflow file that is accessible by the WES
    endpoint, or a relative URL corresponding to one of the files attached using `workflow_attachment`.
    The `workflow_params` JSON object specifies input parameters, such as input files.  The exact format
    of the JSON object depends on the conventions of the workflow language being used.  Input files
    should either be absolute URLs, or relative URLs corresponding to files uploaded using
    `workflow_attachment`.  The WES endpoint must understand and be able to access URLs supplied in the
    input.  This is implementation specific.
    The `workflow_type` is the type of workflow language and must be \"CWL\" or \"WDL\" currently (or
    another alternative  supported by this WES instance).
    The `workflow_type_version` is the version of the workflow language submitted and must be one
    supported by this WES instance.
    The `workflow_engine` is the engine that supports the workflow_type and must be supported by this
    WES instance.
    The `workflow_engine_version` is the version of workflow engine and must be supported by this WES
    instance.
    See the `RunRequest` documentation for details about other fields.

    Args:
        body (RunWorkflowBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | RunId]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: RunWorkflowBody | Unset = UNSET,
) -> ErrorResponse | RunId | None:
    r"""RunWorkflow

     This endpoint creates a new workflow run and returns a `RunId` to monitor its progress.
    The `workflow_attachment` array may be used to upload files that are required to execute the
    workflow, including the primary workflow, tools imported by the workflow, other files referenced by
    the workflow, or files which are part of the input.  The implementation should stage these files to
    a temporary directory and execute the workflow from there. These parts must have a Content-
    Disposition header with a \"filename\" provided for each part.  Filenames may include
    subdirectories, but must not include references to parent directories with '..' -- implementations
    should guard against maliciously constructed filenames.
    The `workflow_url` is either an absolute URL to a workflow file that is accessible by the WES
    endpoint, or a relative URL corresponding to one of the files attached using `workflow_attachment`.
    The `workflow_params` JSON object specifies input parameters, such as input files.  The exact format
    of the JSON object depends on the conventions of the workflow language being used.  Input files
    should either be absolute URLs, or relative URLs corresponding to files uploaded using
    `workflow_attachment`.  The WES endpoint must understand and be able to access URLs supplied in the
    input.  This is implementation specific.
    The `workflow_type` is the type of workflow language and must be \"CWL\" or \"WDL\" currently (or
    another alternative  supported by this WES instance).
    The `workflow_type_version` is the version of the workflow language submitted and must be one
    supported by this WES instance.
    The `workflow_engine` is the engine that supports the workflow_type and must be supported by this
    WES instance.
    The `workflow_engine_version` is the version of workflow engine and must be supported by this WES
    instance.
    See the `RunRequest` documentation for details about other fields.

    Args:
        body (RunWorkflowBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | RunId
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RunWorkflowBody | Unset = UNSET,
) -> Response[ErrorResponse | RunId]:
    r"""RunWorkflow

     This endpoint creates a new workflow run and returns a `RunId` to monitor its progress.
    The `workflow_attachment` array may be used to upload files that are required to execute the
    workflow, including the primary workflow, tools imported by the workflow, other files referenced by
    the workflow, or files which are part of the input.  The implementation should stage these files to
    a temporary directory and execute the workflow from there. These parts must have a Content-
    Disposition header with a \"filename\" provided for each part.  Filenames may include
    subdirectories, but must not include references to parent directories with '..' -- implementations
    should guard against maliciously constructed filenames.
    The `workflow_url` is either an absolute URL to a workflow file that is accessible by the WES
    endpoint, or a relative URL corresponding to one of the files attached using `workflow_attachment`.
    The `workflow_params` JSON object specifies input parameters, such as input files.  The exact format
    of the JSON object depends on the conventions of the workflow language being used.  Input files
    should either be absolute URLs, or relative URLs corresponding to files uploaded using
    `workflow_attachment`.  The WES endpoint must understand and be able to access URLs supplied in the
    input.  This is implementation specific.
    The `workflow_type` is the type of workflow language and must be \"CWL\" or \"WDL\" currently (or
    another alternative  supported by this WES instance).
    The `workflow_type_version` is the version of the workflow language submitted and must be one
    supported by this WES instance.
    The `workflow_engine` is the engine that supports the workflow_type and must be supported by this
    WES instance.
    The `workflow_engine_version` is the version of workflow engine and must be supported by this WES
    instance.
    See the `RunRequest` documentation for details about other fields.

    Args:
        body (RunWorkflowBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | RunId]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: RunWorkflowBody | Unset = UNSET,
) -> ErrorResponse | RunId | None:
    r"""RunWorkflow

     This endpoint creates a new workflow run and returns a `RunId` to monitor its progress.
    The `workflow_attachment` array may be used to upload files that are required to execute the
    workflow, including the primary workflow, tools imported by the workflow, other files referenced by
    the workflow, or files which are part of the input.  The implementation should stage these files to
    a temporary directory and execute the workflow from there. These parts must have a Content-
    Disposition header with a \"filename\" provided for each part.  Filenames may include
    subdirectories, but must not include references to parent directories with '..' -- implementations
    should guard against maliciously constructed filenames.
    The `workflow_url` is either an absolute URL to a workflow file that is accessible by the WES
    endpoint, or a relative URL corresponding to one of the files attached using `workflow_attachment`.
    The `workflow_params` JSON object specifies input parameters, such as input files.  The exact format
    of the JSON object depends on the conventions of the workflow language being used.  Input files
    should either be absolute URLs, or relative URLs corresponding to files uploaded using
    `workflow_attachment`.  The WES endpoint must understand and be able to access URLs supplied in the
    input.  This is implementation specific.
    The `workflow_type` is the type of workflow language and must be \"CWL\" or \"WDL\" currently (or
    another alternative  supported by this WES instance).
    The `workflow_type_version` is the version of the workflow language submitted and must be one
    supported by this WES instance.
    The `workflow_engine` is the engine that supports the workflow_type and must be supported by this
    WES instance.
    The `workflow_engine_version` is the version of workflow engine and must be supported by this WES
    instance.
    See the `RunRequest` documentation for details about other fields.

    Args:
        body (RunWorkflowBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | RunId
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
