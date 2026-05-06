from fastapi.routing import APIRoute

from wes_api_gateway.main import app
from wes_api_gateway.models import (
    RunId,
    RunListResponse,
    RunLog,
    RunStatus,
    ServiceInfo,
    TaskListResponse,
    TaskLog,
)


def api_routes() -> dict[tuple[str, str], APIRoute]:
    routes: dict[tuple[str, str], APIRoute] = {}
    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in route.methods:
                routes[(method, route.path)] = route
    return routes


def resolve_schema_ref(openapi_schema: dict, schema: dict) -> dict:
    ref = schema.get("$ref")
    if ref is None:
        return schema

    prefix = "#/components/schemas/"
    assert ref.startswith(prefix)
    return openapi_schema["components"]["schemas"][ref.removeprefix(prefix)]


def test_app_exposes_wes_service_metadata() -> None:
    assert app.title == "Workflow Execution Service"
    assert app.version == "1.1.0"
    assert app.servers == [
        {
            "url": "https://{defaultHost}/{basePath}/{apiVersion}",
            "variables": {
                "defaultHost": {"default": "www.example.com"},
                "basePath": {"default": "ga4gh/wes"},
                "apiVersion": {"default": "v1"},
            },
        }
    ]


def test_wes_routes_are_registered_with_expected_response_models() -> None:
    routes = api_routes()

    expected_routes = {
        ("GET", "/service-info"): ServiceInfo,
        ("GET", "/runs"): RunListResponse,
        ("POST", "/runs"): RunId,
        ("GET", "/runs/{run_id}"): RunLog,
        ("GET", "/runs/{run_id}/status"): RunStatus,
        ("POST", "/runs/{run_id}/cancel"): RunId,
        ("GET", "/runs/{run_id}/tasks"): TaskListResponse,
        ("GET", "/runs/{run_id}/tasks/{task_id}"): TaskLog,
    }

    assert set(expected_routes).issubset(routes)
    for route_key, response_model in expected_routes.items():
        assert routes[route_key].response_model is response_model


def test_openapi_schema_contains_wes_paths_and_multipart_submission() -> None:
    schema = app.openapi()

    assert schema["info"]["title"] == "Workflow Execution Service"
    assert schema["info"]["version"] == "1.1.0"
    assert set(schema["paths"]) >= {
        "/service-info",
        "/runs",
        "/runs/{run_id}",
        "/runs/{run_id}/status",
        "/runs/{run_id}/cancel",
        "/runs/{run_id}/tasks",
        "/runs/{run_id}/tasks/{task_id}",
    }

    run_submission = schema["paths"]["/runs"]["post"]
    content = run_submission["requestBody"]["content"]
    multipart_schema = resolve_schema_ref(
        schema, content["multipart/form-data"]["schema"]
    )

    assert multipart_schema["properties"]["workflow_attachment"] == {
        "items": {"type": "string", "format": "binary"},
        "type": "array",
        "title": "Workflow Attachment",
    }
