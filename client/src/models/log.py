from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Log")


@_attrs_define
class Log:
    """Log and other info

    Attributes:
        name (str | Unset): The task or workflow name
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
            which are not tied directly to a workflow.
            Content is implementation specific: format, size, etc.

            System logs may be collected here to provide convenient access.

            For example, the system may include an error message that caused
            a SYSTEM_ERROR state (e.g. disk is full), etc.
    """

    name: str | Unset = UNSET
    cmd: list[str] | Unset = UNSET
    start_time: str | Unset = UNSET
    end_time: str | Unset = UNSET
    stdout: str | Unset = UNSET
    stderr: str | Unset = UNSET
    exit_code: int | Unset = UNSET
    system_logs: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        cmd = cast(list[str], d.pop("cmd", UNSET))

        start_time = d.pop("start_time", UNSET)

        end_time = d.pop("end_time", UNSET)

        stdout = d.pop("stdout", UNSET)

        stderr = d.pop("stderr", UNSET)

        exit_code = d.pop("exit_code", UNSET)

        system_logs = cast(list[str], d.pop("system_logs", UNSET))

        log = cls(
            name=name,
            cmd=cmd,
            start_time=start_time,
            end_time=end_time,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            system_logs=system_logs,
        )

        log.additional_properties = d
        return log

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
