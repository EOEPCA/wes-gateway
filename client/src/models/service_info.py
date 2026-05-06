from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.default_workflow_engine_parameter import (
        DefaultWorkflowEngineParameter,
    )
    from ..models.service_info_system_state_counts import ServiceInfoSystemStateCounts
    from ..models.service_info_tags import ServiceInfoTags
    from ..models.service_info_workflow_engine_versions import (
        ServiceInfoWorkflowEngineVersions,
    )
    from ..models.service_info_workflow_type_versions import (
        ServiceInfoWorkflowTypeVersions,
    )
    from ..models.service_organization import ServiceOrganization
    from ..models.service_type import ServiceType


T = TypeVar("T", bound="ServiceInfo")


@_attrs_define
class ServiceInfo:
    """
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
        workflow_type_versions (ServiceInfoWorkflowTypeVersions):
        supported_wes_versions (list[str]): The version(s) of the WES schema supported by this service
        supported_filesystem_protocols (list[str]): The filesystem protocols supported by this service, currently these
            may include common protocols using the terms 'http', 'https', 'sftp', 's3', 'gs', 'file', or 'synapse', but
            others  are possible and the terms beyond these core protocols are currently not fixed.   This section reports
            those protocols (either common or not) supported by this WES service.
        workflow_engine_versions (ServiceInfoWorkflowEngineVersions):
        default_workflow_engine_parameters (list[DefaultWorkflowEngineParameter]): Each workflow engine can present
            additional parameters that can be sent to the workflow engine. This message will list the default values, and
            their types for each workflow engine.
        system_state_counts (ServiceInfoSystemStateCounts):
        auth_instructions_url (str): A web page URL with human-readable instructions on how to get an authorization
            token for use with a specific WES endpoint.
        tags (ServiceInfoTags):
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
    workflow_type_versions: ServiceInfoWorkflowTypeVersions
    supported_wes_versions: list[str]
    supported_filesystem_protocols: list[str]
    workflow_engine_versions: ServiceInfoWorkflowEngineVersions
    default_workflow_engine_parameters: list[DefaultWorkflowEngineParameter]
    system_state_counts: ServiceInfoSystemStateCounts
    auth_instructions_url: str
    tags: ServiceInfoTags
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

        workflow_type_versions = self.workflow_type_versions.to_dict()

        supported_wes_versions = self.supported_wes_versions

        supported_filesystem_protocols = self.supported_filesystem_protocols

        workflow_engine_versions = self.workflow_engine_versions.to_dict()

        default_workflow_engine_parameters = []
        for (
            default_workflow_engine_parameters_item_data
        ) in self.default_workflow_engine_parameters:
            default_workflow_engine_parameters_item = (
                default_workflow_engine_parameters_item_data.to_dict()
            )
            default_workflow_engine_parameters.append(
                default_workflow_engine_parameters_item
            )

        system_state_counts = self.system_state_counts.to_dict()

        auth_instructions_url = self.auth_instructions_url

        tags = self.tags.to_dict()

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
                "workflow_type_versions": workflow_type_versions,
                "supported_wes_versions": supported_wes_versions,
                "supported_filesystem_protocols": supported_filesystem_protocols,
                "workflow_engine_versions": workflow_engine_versions,
                "default_workflow_engine_parameters": default_workflow_engine_parameters,
                "system_state_counts": system_state_counts,
                "auth_instructions_url": auth_instructions_url,
                "tags": tags,
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
        from ..models.default_workflow_engine_parameter import (
            DefaultWorkflowEngineParameter,
        )
        from ..models.service_info_system_state_counts import (
            ServiceInfoSystemStateCounts,
        )
        from ..models.service_info_tags import ServiceInfoTags
        from ..models.service_info_workflow_engine_versions import (
            ServiceInfoWorkflowEngineVersions,
        )
        from ..models.service_info_workflow_type_versions import (
            ServiceInfoWorkflowTypeVersions,
        )
        from ..models.service_organization import ServiceOrganization
        from ..models.service_type import ServiceType

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        type_ = ServiceType.from_dict(d.pop("type"))

        organization = ServiceOrganization.from_dict(d.pop("organization"))

        version = d.pop("version")

        workflow_type_versions = ServiceInfoWorkflowTypeVersions.from_dict(
            d.pop("workflow_type_versions")
        )

        supported_wes_versions = cast(list[str], d.pop("supported_wes_versions"))

        supported_filesystem_protocols = cast(
            list[str], d.pop("supported_filesystem_protocols")
        )

        workflow_engine_versions = ServiceInfoWorkflowEngineVersions.from_dict(
            d.pop("workflow_engine_versions")
        )

        default_workflow_engine_parameters = []
        _default_workflow_engine_parameters = d.pop(
            "default_workflow_engine_parameters"
        )
        for (
            default_workflow_engine_parameters_item_data
        ) in _default_workflow_engine_parameters:
            default_workflow_engine_parameters_item = (
                DefaultWorkflowEngineParameter.from_dict(
                    default_workflow_engine_parameters_item_data
                )
            )

            default_workflow_engine_parameters.append(
                default_workflow_engine_parameters_item
            )

        system_state_counts = ServiceInfoSystemStateCounts.from_dict(
            d.pop("system_state_counts")
        )

        auth_instructions_url = d.pop("auth_instructions_url")

        tags = ServiceInfoTags.from_dict(d.pop("tags"))

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

        service_info = cls(
            id=id,
            name=name,
            type_=type_,
            organization=organization,
            version=version,
            workflow_type_versions=workflow_type_versions,
            supported_wes_versions=supported_wes_versions,
            supported_filesystem_protocols=supported_filesystem_protocols,
            workflow_engine_versions=workflow_engine_versions,
            default_workflow_engine_parameters=default_workflow_engine_parameters,
            system_state_counts=system_state_counts,
            auth_instructions_url=auth_instructions_url,
            tags=tags,
            description=description,
            contact_url=contact_url,
            documentation_url=documentation_url,
            created_at=created_at,
            updated_at=updated_at,
            environment=environment,
        )

        service_info.additional_properties = d
        return service_info

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
