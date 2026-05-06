from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkflowEngineVersion")


@_attrs_define
class WorkflowEngineVersion:
    """Available workflow engine versions supported by a given instance of the service.

    Attributes:
        workflow_engine_version (list[str] | Unset): An array of one or more acceptable engines versions for the
            `workflow_engine`
    """

    workflow_engine_version: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workflow_engine_version: list[str] | Unset = UNSET
        if not isinstance(self.workflow_engine_version, Unset):
            workflow_engine_version = self.workflow_engine_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if workflow_engine_version is not UNSET:
            field_dict["workflow_engine_version"] = workflow_engine_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workflow_engine_version = cast(
            list[str], d.pop("workflow_engine_version", UNSET)
        )

        workflow_engine_version = cls(
            workflow_engine_version=workflow_engine_version,
        )

        workflow_engine_version.additional_properties = d
        return workflow_engine_version

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
