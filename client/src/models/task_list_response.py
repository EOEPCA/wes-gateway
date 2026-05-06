from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.task_log import TaskLog


T = TypeVar("T", bound="TaskListResponse")


@_attrs_define
class TaskListResponse:
    """The service will return a TaskListResponse when receiving a successful TaskListRequest.

    Attributes:
        task_logs (list[TaskLog] | Unset): The logs, and other key info like timing and exit code, for each step in the
            workflow run.
        next_page_token (str | Unset): A token which may be supplied as `page_token` in workflow run task list request
            to get the next page of results.  An empty string indicates there are no more items to return.
    """

    task_logs: list[TaskLog] | Unset = UNSET
    next_page_token: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        task_logs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.task_logs, Unset):
            task_logs = []
            for task_logs_item_data in self.task_logs:
                task_logs_item = task_logs_item_data.to_dict()
                task_logs.append(task_logs_item)

        next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if task_logs is not UNSET:
            field_dict["task_logs"] = task_logs
        if next_page_token is not UNSET:
            field_dict["next_page_token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_log import TaskLog

        d = dict(src_dict)
        _task_logs = d.pop("task_logs", UNSET)
        task_logs: list[TaskLog] | Unset = UNSET
        if _task_logs is not UNSET:
            task_logs = []
            for task_logs_item_data in _task_logs:
                task_logs_item = TaskLog.from_dict(task_logs_item_data)

                task_logs.append(task_logs_item)

        next_page_token = d.pop("next_page_token", UNSET)

        task_list_response = cls(
            task_logs=task_logs,
            next_page_token=next_page_token,
        )

        task_list_response.additional_properties = d
        return task_list_response

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
