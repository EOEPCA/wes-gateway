from __future__ import annotations

from collections.abc import Mapping
from io import BytesIO
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, File, FileTypes, Unset

T = TypeVar("T", bound="RunWorkflowBody")


@_attrs_define
class RunWorkflowBody:
    """
    Attributes:
        workflow_params (str | Unset):
        workflow_type (str | Unset):
        workflow_type_version (str | Unset):
        tags (str | Unset):
        workflow_engine (str | Unset):
        workflow_engine_version (str | Unset):
        workflow_engine_parameters (str | Unset):
        workflow_url (str | Unset):
        workflow_attachment (list[File] | Unset):
    """

    workflow_params: str | Unset = UNSET
    workflow_type: str | Unset = UNSET
    workflow_type_version: str | Unset = UNSET
    tags: str | Unset = UNSET
    workflow_engine: str | Unset = UNSET
    workflow_engine_version: str | Unset = UNSET
    workflow_engine_parameters: str | Unset = UNSET
    workflow_url: str | Unset = UNSET
    workflow_attachment: list[File] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workflow_params = self.workflow_params

        workflow_type = self.workflow_type

        workflow_type_version = self.workflow_type_version

        tags = self.tags

        workflow_engine = self.workflow_engine

        workflow_engine_version = self.workflow_engine_version

        workflow_engine_parameters = self.workflow_engine_parameters

        workflow_url = self.workflow_url

        workflow_attachment: list[FileTypes] | Unset = UNSET
        if not isinstance(self.workflow_attachment, Unset):
            workflow_attachment = []
            for workflow_attachment_item_data in self.workflow_attachment:
                workflow_attachment_item = workflow_attachment_item_data.to_tuple()

                workflow_attachment.append(workflow_attachment_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if workflow_params is not UNSET:
            field_dict["workflow_params"] = workflow_params
        if workflow_type is not UNSET:
            field_dict["workflow_type"] = workflow_type
        if workflow_type_version is not UNSET:
            field_dict["workflow_type_version"] = workflow_type_version
        if tags is not UNSET:
            field_dict["tags"] = tags
        if workflow_engine is not UNSET:
            field_dict["workflow_engine"] = workflow_engine
        if workflow_engine_version is not UNSET:
            field_dict["workflow_engine_version"] = workflow_engine_version
        if workflow_engine_parameters is not UNSET:
            field_dict["workflow_engine_parameters"] = workflow_engine_parameters
        if workflow_url is not UNSET:
            field_dict["workflow_url"] = workflow_url
        if workflow_attachment is not UNSET:
            field_dict["workflow_attachment"] = workflow_attachment

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        if not isinstance(self.workflow_params, Unset):
            files.append(
                (
                    "workflow_params",
                    (None, str(self.workflow_params).encode(), "text/plain"),
                )
            )

        if not isinstance(self.workflow_type, Unset):
            files.append(
                (
                    "workflow_type",
                    (None, str(self.workflow_type).encode(), "text/plain"),
                )
            )

        if not isinstance(self.workflow_type_version, Unset):
            files.append(
                (
                    "workflow_type_version",
                    (None, str(self.workflow_type_version).encode(), "text/plain"),
                )
            )

        if not isinstance(self.tags, Unset):
            files.append(("tags", (None, str(self.tags).encode(), "text/plain")))

        if not isinstance(self.workflow_engine, Unset):
            files.append(
                (
                    "workflow_engine",
                    (None, str(self.workflow_engine).encode(), "text/plain"),
                )
            )

        if not isinstance(self.workflow_engine_version, Unset):
            files.append(
                (
                    "workflow_engine_version",
                    (None, str(self.workflow_engine_version).encode(), "text/plain"),
                )
            )

        if not isinstance(self.workflow_engine_parameters, Unset):
            files.append(
                (
                    "workflow_engine_parameters",
                    (None, str(self.workflow_engine_parameters).encode(), "text/plain"),
                )
            )

        if not isinstance(self.workflow_url, Unset):
            files.append(
                ("workflow_url", (None, str(self.workflow_url).encode(), "text/plain"))
            )

        if not isinstance(self.workflow_attachment, Unset):
            for workflow_attachment_item_element in self.workflow_attachment:
                files.append(
                    ("workflow_attachment", workflow_attachment_item_element.to_tuple())
                )

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workflow_params = d.pop("workflow_params", UNSET)

        workflow_type = d.pop("workflow_type", UNSET)

        workflow_type_version = d.pop("workflow_type_version", UNSET)

        tags = d.pop("tags", UNSET)

        workflow_engine = d.pop("workflow_engine", UNSET)

        workflow_engine_version = d.pop("workflow_engine_version", UNSET)

        workflow_engine_parameters = d.pop("workflow_engine_parameters", UNSET)

        workflow_url = d.pop("workflow_url", UNSET)

        _workflow_attachment = d.pop("workflow_attachment", UNSET)
        workflow_attachment: list[File] | Unset = UNSET
        if _workflow_attachment is not UNSET:
            workflow_attachment = []
            for workflow_attachment_item_data in _workflow_attachment:
                workflow_attachment_item = File(
                    payload=BytesIO(workflow_attachment_item_data)
                )

                workflow_attachment.append(workflow_attachment_item)

        run_workflow_body = cls(
            workflow_params=workflow_params,
            workflow_type=workflow_type,
            workflow_type_version=workflow_type_version,
            tags=tags,
            workflow_engine=workflow_engine,
            workflow_engine_version=workflow_engine_version,
            workflow_engine_parameters=workflow_engine_parameters,
            workflow_url=workflow_url,
            workflow_attachment=workflow_attachment,
        )

        run_workflow_body.additional_properties = d
        return run_workflow_body

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
