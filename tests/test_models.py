import pytest
from pydantic import ValidationError

from wes_api_gateway.models import (
    DefaultWorkflowEngineParameter,
    Log,
    RunLog,
    RunRequest,
    RunStatus,
    ServiceInfo,
    State,
    TaskLog,
    WorkflowEngineVersion,
    WorkflowTypeVersion,
)


def test_state_enum_matches_wes_state_vocabulary() -> None:
    assert [state.value for state in State] == [
        "UNKNOWN",
        "QUEUED",
        "INITIALIZING",
        "RUNNING",
        "PAUSED",
        "COMPLETE",
        "EXECUTOR_ERROR",
        "SYSTEM_ERROR",
        "CANCELED",
        "CANCELING",
        "PREEMPTED",
    ]


def test_run_request_requires_workflow_identity_fields() -> None:
    request = RunRequest(
        workflow_type="CWL",
        workflow_type_version="v1.0",
        workflow_url="workflow.cwl",
        workflow_params={"message": "hello"},
        tags={"project": "demo"},
        workflow_engine="toil",
        workflow_engine_parameters={"--logLevel": "INFO"},
    )

    assert request.model_dump() == {
        "workflow_params": {"message": "hello"},
        "workflow_type": "CWL",
        "workflow_type_version": "v1.0",
        "tags": {"project": "demo"},
        "workflow_engine_parameters": {"--logLevel": "INFO"},
        "workflow_engine": "toil",
        "workflow_engine_version": None,
        "workflow_url": "workflow.cwl",
    }

    with pytest.raises(ValidationError):
        RunRequest(workflow_type="CWL", workflow_url="workflow.cwl")


def test_run_status_serializes_state_values_for_api_responses() -> None:
    status = RunStatus(run_id="run-001", state=State.RUNNING)

    assert status.model_dump(mode="json") == {
        "run_id": "run-001",
        "state": "RUNNING",
    }


def test_run_log_can_include_request_logs_tasks_and_outputs() -> None:
    request = RunRequest(
        workflow_type="CWL",
        workflow_type_version="v1.0",
        workflow_url="workflow.cwl",
    )
    task = TaskLog(
        id="task-001",
        name="echo",
        cmd=["echo", "hello"],
        exit_code=0,
        stdout="https://example.org/stdout",
        stderr="https://example.org/stderr",
    )
    run_log = RunLog(
        run_id="run-001",
        request=request,
        state=State.COMPLETE,
        run_log=Log(name="workflow", exit_code=0),
        task_logs=[task],
        outputs={"output": "s3://bucket/output.txt"},
    )

    data = run_log.model_dump(mode="json")

    assert data["state"] == "COMPLETE"
    assert data["task_logs"] == [task.model_dump(mode="json")]
    assert run_log.outputs == {"output": "s3://bucket/output.txt"}


def test_service_info_models_toil_backed_wes_capabilities() -> None:
    service_info = ServiceInfo(
        id="org.eoepca.wes-gateway",
        name="WES API Gateway",
        type={"group": "org.ga4gh", "artifact": "wes", "version": "1.1.0"},
        organization={"name": "EOEPCA", "url": "https://eoepca.org"},
        version="0.0.1",
        workflow_type_versions={
            "CWL": WorkflowTypeVersion(workflow_type_version=["v1.0", "v1.1"])
        },
        supported_wes_versions=["1.1.0"],
        supported_filesystem_protocols=["http", "https", "s3"],
        workflow_engine_versions={
            "toil": WorkflowEngineVersion(workflow_engine_version=["8.0.0"])
        },
        default_workflow_engine_parameters=[
            DefaultWorkflowEngineParameter(
                name="--logLevel",
                type="string",
                default_value="INFO",
            )
        ],
        system_state_counts={"RUNNING": 1, "COMPLETE": 2},
        auth_instructions_url="https://example.org/auth",
        tags={"runner": "toil"},
    )

    data = service_info.model_dump(mode="json")

    assert data["type"]["artifact"] == "wes"
    assert data["workflow_engine_versions"] == {
        "toil": {"workflow_engine_version": ["8.0.0"]}
    }
    assert data["tags"] == {"runner": "toil"}
