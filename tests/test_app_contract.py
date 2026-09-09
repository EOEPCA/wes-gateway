from wes_api_gateway.main import app


def test_namespaced_wes_contract():
    schema = app.openapi()
    assert schema["info"]["title"] == "Workflow Execution Service"
    base = "/wes/v1/{namespace}"
    assert set(schema["paths"]) >= {
        base + "/service-info",
        base + "/runs",
        base + "/runs/{run_id}",
        base + "/runs/{run_id}/status",
        base + "/runs/{run_id}/cancel",
        base + "/runs/{run_id}/tasks",
        base + "/runs/{run_id}/tasks/{task_id}",
    }
    content = schema["paths"][base + "/runs"]["post"]["requestBody"]["content"]
    submission = content["multipart/form-data"]["schema"]
    assert set(submission["required"]) == {
        "workflow_url",
        "workflow_type",
        "workflow_type_version",
        "workflow_params",
    }
    assert submission["properties"]["workflow_attachment"]["items"] == {
        "type": "string",
        "format": "binary",
    }
