from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ServiceType")


@_attrs_define
class ServiceType:
    """Type of a GA4GH service

    Attributes:
        group (str): Namespace in reverse domain name format. Use `org.ga4gh` for implementations compliant with
            official GA4GH specifications. For services with custom APIs not standardized by GA4GH, or implementations
            diverging from official GA4GH specifications, use a different namespace (e.g. your organization's reverse domain
            name). Example: org.ga4gh.
        artifact (str): Name of the API or GA4GH specification implemented. Official GA4GH types should be assigned as
            part of standards approval process. Custom artifacts are supported. Example: beacon.
        version (str): Version of the API or specification. GA4GH specifications use semantic versioning. Example:
            1.0.0.
    """

    group: str
    artifact: str
    version: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        group = self.group

        artifact = self.artifact

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "group": group,
                "artifact": artifact,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        group = d.pop("group")

        artifact = d.pop("artifact")

        version = d.pop("version")

        service_type = cls(
            group=group,
            artifact=artifact,
            version=version,
        )

        service_type.additional_properties = d
        return service_type

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
