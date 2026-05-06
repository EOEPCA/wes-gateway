from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DefaultWorkflowEngineParameter")


@_attrs_define
class DefaultWorkflowEngineParameter:
    """A message that allows one to describe default parameters for a workflow engine.

    Attributes:
        name (str | Unset): The name of the parameter
        type_ (str | Unset): Describes the type of the parameter, e.g. float.
        default_value (str | Unset): The stringified version of the default parameter. e.g. "2.45".
    """

    name: str | Unset = UNSET
    type_: str | Unset = UNSET
    default_value: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_

        default_value = self.default_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if type_ is not UNSET:
            field_dict["type"] = type_
        if default_value is not UNSET:
            field_dict["default_value"] = default_value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        type_ = d.pop("type", UNSET)

        default_value = d.pop("default_value", UNSET)

        default_workflow_engine_parameter = cls(
            name=name,
            type_=type_,
            default_value=default_value,
        )

        default_workflow_engine_parameter.additional_properties = d
        return default_workflow_engine_parameter

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
