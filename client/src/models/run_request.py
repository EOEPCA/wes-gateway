from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_request_tags import RunRequestTags
    from ..models.run_request_workflow_engine_parameters import (
        RunRequestWorkflowEngineParameters,
    )
    from ..models.run_request_workflow_params import RunRequestWorkflowParams


T = TypeVar("T", bound="RunRequest")


@_attrs_define
class RunRequest:
    """To execute a workflow, send a run request including all the details needed to begin downloading
    and executing a given workflow.
    If workflow_engine and workflow_engine_version are not provided, servers can use the most recent
    workflow_engine_version of workflow_engine that WES instance uses to process the request if
    supports for the requested workflow_type.

        Attributes:
            workflow_type (str): REQUIRED
                The workflow descriptor type, must be "CWL" or "WDL" currently (or another alternative supported by this WES
                instance)
            workflow_type_version (str): REQUIRED
                The workflow descriptor type version, must be one supported by this WES instance
            workflow_url (str): REQUIRED
                The workflow CWL or WDL document. When `workflow_attachments` is used to attach files, the `workflow_url` may be
                a relative path to one of the attachments.
            workflow_params (RunRequestWorkflowParams | Unset): REQUIRED
                The workflow run parameterizations (JSON encoded), including input and output file locations
            tags (RunRequestTags | Unset):
            workflow_engine_parameters (RunRequestWorkflowEngineParameters | Unset):
            workflow_engine (str | Unset): The workflow engine, must be one supported by this WES instance. Required if
                workflow_engine_version is provided.
            workflow_engine_version (str | Unset): The workflow engine version, must be one supported by this WES instance.
                If workflow_engine is provided, but workflow_engine_version is not, servers can make no assumptions with regard
                to the engine version the WES instance uses to process the request if  that WES instance supports multiple
                versions of the requested engine.
    """

    workflow_type: str
    workflow_type_version: str
    workflow_url: str
    workflow_params: RunRequestWorkflowParams | Unset = UNSET
    tags: RunRequestTags | Unset = UNSET
    workflow_engine_parameters: RunRequestWorkflowEngineParameters | Unset = UNSET
    workflow_engine: str | Unset = UNSET
    workflow_engine_version: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workflow_type = self.workflow_type

        workflow_type_version = self.workflow_type_version

        workflow_url = self.workflow_url

        workflow_params: dict[str, Any] | Unset = UNSET
        if not isinstance(self.workflow_params, Unset):
            workflow_params = self.workflow_params.to_dict()

        tags: dict[str, Any] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        workflow_engine_parameters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.workflow_engine_parameters, Unset):
            workflow_engine_parameters = self.workflow_engine_parameters.to_dict()

        workflow_engine = self.workflow_engine

        workflow_engine_version = self.workflow_engine_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workflow_type": workflow_type,
                "workflow_type_version": workflow_type_version,
                "workflow_url": workflow_url,
            }
        )
        if workflow_params is not UNSET:
            field_dict["workflow_params"] = workflow_params
        if tags is not UNSET:
            field_dict["tags"] = tags
        if workflow_engine_parameters is not UNSET:
            field_dict["workflow_engine_parameters"] = workflow_engine_parameters
        if workflow_engine is not UNSET:
            field_dict["workflow_engine"] = workflow_engine
        if workflow_engine_version is not UNSET:
            field_dict["workflow_engine_version"] = workflow_engine_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_request_tags import RunRequestTags
        from ..models.run_request_workflow_engine_parameters import (
            RunRequestWorkflowEngineParameters,
        )
        from ..models.run_request_workflow_params import RunRequestWorkflowParams

        d = dict(src_dict)
        workflow_type = d.pop("workflow_type")

        workflow_type_version = d.pop("workflow_type_version")

        workflow_url = d.pop("workflow_url")

        _workflow_params = d.pop("workflow_params", UNSET)
        workflow_params: RunRequestWorkflowParams | Unset
        if isinstance(_workflow_params, Unset):
            workflow_params = UNSET
        else:
            workflow_params = RunRequestWorkflowParams.from_dict(_workflow_params)

        _tags = d.pop("tags", UNSET)
        tags: RunRequestTags | Unset
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = RunRequestTags.from_dict(_tags)

        _workflow_engine_parameters = d.pop("workflow_engine_parameters", UNSET)
        workflow_engine_parameters: RunRequestWorkflowEngineParameters | Unset
        if isinstance(_workflow_engine_parameters, Unset):
            workflow_engine_parameters = UNSET
        else:
            workflow_engine_parameters = RunRequestWorkflowEngineParameters.from_dict(
                _workflow_engine_parameters
            )

        workflow_engine = d.pop("workflow_engine", UNSET)

        workflow_engine_version = d.pop("workflow_engine_version", UNSET)

        run_request = cls(
            workflow_type=workflow_type,
            workflow_type_version=workflow_type_version,
            workflow_url=workflow_url,
            workflow_params=workflow_params,
            tags=tags,
            workflow_engine_parameters=workflow_engine_parameters,
            workflow_engine=workflow_engine,
            workflow_engine_version=workflow_engine_version,
        )

        run_request.additional_properties = d
        return run_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
