from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkflowTypeVersion")


@_attrs_define
class WorkflowTypeVersion:
    """Available workflow types supported by a given instance of the service.

    Attributes:
        workflow_type_version (list[str] | Unset): an array of one or more acceptable types for the `workflow_type`
    """

    workflow_type_version: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workflow_type_version: list[str] | Unset = UNSET
        if not isinstance(self.workflow_type_version, Unset):
            workflow_type_version = self.workflow_type_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if workflow_type_version is not UNSET:
            field_dict["workflow_type_version"] = workflow_type_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workflow_type_version = cast(list[str], d.pop("workflow_type_version", UNSET))

        workflow_type_version = cls(
            workflow_type_version=workflow_type_version,
        )

        workflow_type_version.additional_properties = d
        return workflow_type_version

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
