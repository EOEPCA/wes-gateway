from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_status import RunStatus
    from ..models.run_summary import RunSummary


T = TypeVar("T", bound="RunListResponse")


@_attrs_define
class RunListResponse:
    """The service will return a RunListResponse when receiving a successful RunListRequest. DEPRECIATION WARNING: The use
    of `RunStatus` as the schema for `runs` array items will not be permitted from the next major version of the
    specification (2.0.0) onwards. We encourage implementers to use `RunSummary` instead.

        Attributes:
            runs (list[RunStatus | RunSummary] | Unset): A list of workflow runs that the service has executed or is
                executing. The list is filtered to only include runs that the caller has permission to see.
            next_page_token (str | Unset): A token which may be supplied as `page_token` in workflow run list request to get
                the next page of results.  An empty string indicates there are no more items to return.
    """

    runs: list[RunStatus | RunSummary] | Unset = UNSET
    next_page_token: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.run_status import RunStatus

        runs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.runs, Unset):
            runs = []
            for runs_item_data in self.runs:
                runs_item: dict[str, Any]
                if isinstance(runs_item_data, RunStatus):
                    runs_item = runs_item_data.to_dict()
                else:
                    runs_item = runs_item_data.to_dict()

                runs.append(runs_item)

        next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if runs is not UNSET:
            field_dict["runs"] = runs
        if next_page_token is not UNSET:
            field_dict["next_page_token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_status import RunStatus
        from ..models.run_summary import RunSummary

        d = dict(src_dict)
        _runs = d.pop("runs", UNSET)
        runs: list[RunStatus | RunSummary] | Unset = UNSET
        if _runs is not UNSET:
            runs = []
            for runs_item_data in _runs:

                def _parse_runs_item(data: object) -> RunStatus | RunSummary:
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        runs_item_type_0 = RunStatus.from_dict(data)

                        return runs_item_type_0
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    if not isinstance(data, dict):
                        raise TypeError()
                    runs_item_type_1 = RunSummary.from_dict(data)

                    return runs_item_type_1

                runs_item = _parse_runs_item(runs_item_data)

                runs.append(runs_item)

        next_page_token = d.pop("next_page_token", UNSET)

        run_list_response = cls(
            runs=runs,
            next_page_token=next_page_token,
        )

        run_list_response.additional_properties = d
        return run_list_response

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
