from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TaskLog")


@_attrs_define
class TaskLog:
    """Runtime information for a given task

    Attributes:
        name (str): The task or workflow name
        id (str): A unique identifier which may be used to reference the task
        cmd (list[str] | Unset): The command line that was executed
        start_time (str | Unset): When the command started executing, in ISO 8601 format "%Y-%m-%dT%H:%M:%SZ"
        end_time (str | Unset): When the command stopped executing (completed, failed, or cancelled), in ISO 8601 format
            "%Y-%m-%dT%H:%M:%SZ"
        stdout (str | Unset): A URL to retrieve standard output logs of the workflow run or task.  This URL may change
            between status requests, or may not be available until the task or workflow has finished execution.  Should be
            available using the same credentials used to access the WES endpoint.
        stderr (str | Unset): A URL to retrieve standard error logs of the workflow run or task.  This URL may change
            between status requests, or may not be available until the task or workflow has finished execution.  Should be
            available using the same credentials used to access the WES endpoint.
        exit_code (int | Unset): Exit code of the program
        system_logs (list[str] | Unset): System logs are any logs the system decides are relevant,
            which are not tied directly to a task.
            Content is implementation specific: format, size, etc.

            System logs may be collected here to provide convenient access.

            For example, the system may include the name of the host
            where the task is executing, an error message that caused
            a SYSTEM_ERROR state (e.g. disk is full), etc.
        tes_uri (str | Unset): An optional URL pointing to an extended task definition defined by a [TES
            api](https://github.com/ga4gh/task-execution-schemas)
    """

    name: str
    id: str
    cmd: list[str] | Unset = UNSET
    start_time: str | Unset = UNSET
    end_time: str | Unset = UNSET
    stdout: str | Unset = UNSET
    stderr: str | Unset = UNSET
    exit_code: int | Unset = UNSET
    system_logs: list[str] | Unset = UNSET
    tes_uri: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id = self.id

        cmd: list[str] | Unset = UNSET
        if not isinstance(self.cmd, Unset):
            cmd = self.cmd

        start_time = self.start_time

        end_time = self.end_time

        stdout = self.stdout

        stderr = self.stderr

        exit_code = self.exit_code

        system_logs: list[str] | Unset = UNSET
        if not isinstance(self.system_logs, Unset):
            system_logs = self.system_logs

        tes_uri = self.tes_uri

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "id": id,
            }
        )
        if cmd is not UNSET:
            field_dict["cmd"] = cmd
        if start_time is not UNSET:
            field_dict["start_time"] = start_time
        if end_time is not UNSET:
            field_dict["end_time"] = end_time
        if stdout is not UNSET:
            field_dict["stdout"] = stdout
        if stderr is not UNSET:
            field_dict["stderr"] = stderr
        if exit_code is not UNSET:
            field_dict["exit_code"] = exit_code
        if system_logs is not UNSET:
            field_dict["system_logs"] = system_logs
        if tes_uri is not UNSET:
            field_dict["tes_uri"] = tes_uri

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        id = d.pop("id")

        cmd = cast(list[str], d.pop("cmd", UNSET))

        start_time = d.pop("start_time", UNSET)

        end_time = d.pop("end_time", UNSET)

        stdout = d.pop("stdout", UNSET)

        stderr = d.pop("stderr", UNSET)

        exit_code = d.pop("exit_code", UNSET)

        system_logs = cast(list[str], d.pop("system_logs", UNSET))

        tes_uri = d.pop("tes_uri", UNSET)

        task_log = cls(
            name=name,
            id=id,
            cmd=cmd,
            start_time=start_time,
            end_time=end_time,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            system_logs=system_logs,
            tes_uri=tes_uri,
        )

        task_log.additional_properties = d
        return task_log

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
