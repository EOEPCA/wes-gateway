from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.state import State
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.log import Log
    from ..models.run_log_outputs import RunLogOutputs
    from ..models.run_request import RunRequest
    from ..models.task_log import TaskLog


T = TypeVar("T", bound="RunLog")


@_attrs_define
class RunLog:
    """
    Attributes:
        run_id (str | Unset): workflow run ID
        request (RunRequest | Unset): To execute a workflow, send a run request including all the details needed to
            begin downloading
            and executing a given workflow.
            If workflow_engine and workflow_engine_version are not provided, servers can use the most recent
            workflow_engine_version of workflow_engine that WES instance uses to process the request if
            supports for the requested workflow_type.
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
        run_log (Log | Unset): Log and other info
        task_logs_url (str | Unset): A reference to the complete url which may be used to obtain a paginated list of
            task logs for this workflow
        task_logs (list[Log | TaskLog] | None | Unset): The logs, and other key info like timing and exit code, for each
            step in the workflow run. This field is deprecated and the `task_logs_url` should be used to retrieve a
            paginated list of steps from the workflow run. This field will be removed in the next major version of the
            specification (2.0.0)
        outputs (RunLogOutputs | Unset): The outputs from the workflow run.
    """

    run_id: str | Unset = UNSET
    request: RunRequest | Unset = UNSET
    state: State | Unset = UNSET
    run_log: Log | Unset = UNSET
    task_logs_url: str | Unset = UNSET
    task_logs: list[Log | TaskLog] | None | Unset = UNSET
    outputs: RunLogOutputs | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.log import Log

        run_id = self.run_id

        request: dict[str, Any] | Unset = UNSET
        if not isinstance(self.request, Unset):
            request = self.request.to_dict()

        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        run_log: dict[str, Any] | Unset = UNSET
        if not isinstance(self.run_log, Unset):
            run_log = self.run_log.to_dict()

        task_logs_url = self.task_logs_url

        task_logs: list[dict[str, Any]] | None | Unset
        if isinstance(self.task_logs, Unset):
            task_logs = UNSET
        elif isinstance(self.task_logs, list):
            task_logs = []
            for task_logs_type_0_item_data in self.task_logs:
                task_logs_type_0_item: dict[str, Any]
                if isinstance(task_logs_type_0_item_data, Log):
                    task_logs_type_0_item = task_logs_type_0_item_data.to_dict()
                else:
                    task_logs_type_0_item = task_logs_type_0_item_data.to_dict()

                task_logs.append(task_logs_type_0_item)

        else:
            task_logs = self.task_logs

        outputs: dict[str, Any] | Unset = UNSET
        if not isinstance(self.outputs, Unset):
            outputs = self.outputs.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if run_id is not UNSET:
            field_dict["run_id"] = run_id
        if request is not UNSET:
            field_dict["request"] = request
        if state is not UNSET:
            field_dict["state"] = state
        if run_log is not UNSET:
            field_dict["run_log"] = run_log
        if task_logs_url is not UNSET:
            field_dict["task_logs_url"] = task_logs_url
        if task_logs is not UNSET:
            field_dict["task_logs"] = task_logs
        if outputs is not UNSET:
            field_dict["outputs"] = outputs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.log import Log
        from ..models.run_log_outputs import RunLogOutputs
        from ..models.run_request import RunRequest
        from ..models.task_log import TaskLog

        d = dict(src_dict)
        run_id = d.pop("run_id", UNSET)

        _request = d.pop("request", UNSET)
        request: RunRequest | Unset
        if isinstance(_request, Unset):
            request = UNSET
        else:
            request = RunRequest.from_dict(_request)

        _state = d.pop("state", UNSET)
        state: State | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = State(_state)

        _run_log = d.pop("run_log", UNSET)
        run_log: Log | Unset
        if isinstance(_run_log, Unset):
            run_log = UNSET
        else:
            run_log = Log.from_dict(_run_log)

        task_logs_url = d.pop("task_logs_url", UNSET)

        def _parse_task_logs(data: object) -> list[Log | TaskLog] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                task_logs_type_0 = []
                _task_logs_type_0 = data
                for task_logs_type_0_item_data in _task_logs_type_0:

                    def _parse_task_logs_type_0_item(data: object) -> Log | TaskLog:
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            task_logs_type_0_item_type_0 = Log.from_dict(data)

                            return task_logs_type_0_item_type_0
                        except (TypeError, ValueError, AttributeError, KeyError):
                            pass
                        if not isinstance(data, dict):
                            raise TypeError()
                        task_logs_type_0_item_type_1 = TaskLog.from_dict(data)

                        return task_logs_type_0_item_type_1

                    task_logs_type_0_item = _parse_task_logs_type_0_item(
                        task_logs_type_0_item_data
                    )

                    task_logs_type_0.append(task_logs_type_0_item)

                return task_logs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[Log | TaskLog] | None | Unset, data)

        task_logs = _parse_task_logs(d.pop("task_logs", UNSET))

        _outputs = d.pop("outputs", UNSET)
        outputs: RunLogOutputs | Unset
        if isinstance(_outputs, Unset):
            outputs = UNSET
        else:
            outputs = RunLogOutputs.from_dict(_outputs)

        run_log = cls(
            run_id=run_id,
            request=request,
            state=state,
            run_log=run_log,
            task_logs_url=task_logs_url,
            task_logs=task_logs,
            outputs=outputs,
        )

        run_log.additional_properties = d
        return run_log

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
