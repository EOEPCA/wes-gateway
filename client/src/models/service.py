from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.service_organization import ServiceOrganization
    from ..models.service_type import ServiceType


T = TypeVar("T", bound="Service")


@_attrs_define
class Service:
    """GA4GH service

    Attributes:
        id (str): Unique ID of this service. Reverse domain name notation is recommended, though not required. The
            identifier should attempt to be globally unique so it can be used in downstream aggregator services e.g. Service
            Registry. Example: org.ga4gh.myservice.
        name (str): Name of this service. Should be human readable. Example: My project.
        type_ (ServiceType): Type of a GA4GH service
        organization (ServiceOrganization): Organization providing the service
        version (str): Version of the service being described. Semantic versioning is recommended, but other
            identifiers, such as dates or commit hashes, are also allowed. The version should be changed whenever the
            service is updated. Example: 1.0.0.
        description (str | Unset): Description of the service. Should be human readable and provide information about
            the service. Example: This service provides....
        contact_url (str | Unset): URL of the contact for the provider of this service, e.g. a link to a contact form
            (RFC 3986 format), or an email (RFC 2368 format). Example: mailto:support@example.com.
        documentation_url (str | Unset): URL of the documentation of this service (RFC 3986 format). This should help
            someone learn how to use your service, including any specifics required to access data, e.g. authentication.
            Example: https://docs.myservice.example.com.
        created_at (datetime.datetime | Unset): Timestamp describing when the service was first deployed and available
            (RFC 3339 format) Example: 2019-06-04T12:58:19Z.
        updated_at (datetime.datetime | Unset): Timestamp describing when the service was last updated (RFC 3339 format)
            Example: 2019-06-04T12:58:19Z.
        environment (str | Unset): Environment the service is running in. Use this to distinguish between production,
            development and testing/staging deployments. Suggested values are prod, test, dev, staging. However this is
            advised and not enforced. Example: test.
    """

    id: str
    name: str
    type_: ServiceType
    organization: ServiceOrganization
    version: str
    description: str | Unset = UNSET
    contact_url: str | Unset = UNSET
    documentation_url: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    environment: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        type_ = self.type_.to_dict()

        organization = self.organization.to_dict()

        version = self.version

        description = self.description

        contact_url = self.contact_url

        documentation_url = self.documentation_url

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        environment = self.environment

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "organization": organization,
                "version": version,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if contact_url is not UNSET:
            field_dict["contactUrl"] = contact_url
        if documentation_url is not UNSET:
            field_dict["documentationUrl"] = documentation_url
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if environment is not UNSET:
            field_dict["environment"] = environment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_organization import ServiceOrganization
        from ..models.service_type import ServiceType

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        type_ = ServiceType.from_dict(d.pop("type"))

        organization = ServiceOrganization.from_dict(d.pop("organization"))

        version = d.pop("version")

        description = d.pop("description", UNSET)

        contact_url = d.pop("contactUrl", UNSET)

        documentation_url = d.pop("documentationUrl", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        environment = d.pop("environment", UNSET)

        service = cls(
            id=id,
            name=name,
            type_=type_,
            organization=organization,
            version=version,
            description=description,
            contact_url=contact_url,
            documentation_url=documentation_url,
            created_at=created_at,
            updated_at=updated_at,
            environment=environment,
        )

        service.additional_properties = d
        return service

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
