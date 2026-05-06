from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.state import State
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_summary_tags import RunSummaryTags


T = TypeVar("T", bound="RunSummary")


@_attrs_define
class RunSummary:
    """Small description of a workflow run

    Attributes:
        run_id (str):
        tags (RunSummaryTags): Arbitrary key/value tags added by the client during run creation
        state (State | Unset): State can take any of the following values:

              + UNKNOWN: The state of the task is unknown. This provides a safe default for messages where this field is
            missing, for example, so that a missing field does not accidentally imply that the state is QUEUED.

              + QUEUED: The task is queued.

              + INITIALIZING: The task has been assigned to a worker and is currently preparing to run. For example, the
            worker may be turning on, downloading input files, etc.

              + RUNNING: The task is running. Input files are downloaded and the first Executor has been started.

              + PAUSED: The task is paused. An implementation may have the ability to pause a task, but this is not
            required.

              + COMPLETE: The task has completed running. Executors have exited without error
              and output files have been successfully uploaded.

              + EXECUTOR_ERROR: The task encountered an error in one of the Executor processes. Generally,
            this means that an Executor exited with a non-zero exit code.

              + SYSTEM_ERROR: The task was stopped due to a system error, but not from an Executor,
            for example an upload failed due to network issues, the worker's ran out of disk space, etc.

              + CANCELED: The task was canceled by the user.

              + CANCELING: The task was canceled by the user, and is in the process of stopping.

              + PREEMPTED: The task is stopped (preempted) by the system. The reasons for this would be tied to
            the specific system running the job. Generally, this means that the system reclaimed the compute capacity for
            reallocation.
        start_time (str | Unset): When the run started executing, in ISO 8601 format "%Y-%m-%dT%H:%M:%SZ"
        end_time (str | Unset): When the run stopped executing (completed, failed, or cancelled), in ISO 8601 format
            "%Y-%m-%dT%H:%M:%SZ"
    """

    run_id: str
    tags: RunSummaryTags
    state: State | Unset = UNSET
    start_time: str | Unset = UNSET
    end_time: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_id = self.run_id

        tags = self.tags.to_dict()

        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        start_time = self.start_time

        end_time = self.end_time

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "run_id": run_id,
                "tags": tags,
            }
        )
        if state is not UNSET:
            field_dict["state"] = state
        if start_time is not UNSET:
            field_dict["start_time"] = start_time
        if end_time is not UNSET:
            field_dict["end_time"] = end_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_summary_tags import RunSummaryTags

        d = dict(src_dict)
        run_id = d.pop("run_id")

        tags = RunSummaryTags.from_dict(d.pop("tags"))

        _state = d.pop("state", UNSET)
        state: State | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = State(_state)

        start_time = d.pop("start_time", UNSET)

        end_time = d.pop("end_time", UNSET)

        run_summary = cls(
            run_id=run_id,
            tags=tags,
            state=state,
            start_time=start_time,
            end_time=end_time,
        )

        run_summary.additional_properties = d
        return run_summary

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
