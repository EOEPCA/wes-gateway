"""Opt-in tests that submit actual workflows to the configured gateway."""

import importlib.util
import json
import os
from pathlib import Path

import httpx
import pytest

BASE = os.environ.get("WES_GATEWAY_URL", "").rstrip("/")
ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    not BASE, reason="Set WES_GATEWAY_URL to a deployed gateway origin"
)
spec = importlib.util.spec_from_file_location(
    "run_workflow", ROOT / "examples/run_workflow.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.mark.parametrize("namespace", ["tenant-a", "tenant-b"])
@pytest.mark.parametrize("case", ["hello", "scatter", "cancel"])
def test_live_workflow(namespace, case):
    directory = ROOT / "examples/cwl"
    expected_file = directory / f"{case}.expected.json"
    run_id = runner.execute(
        f"{BASE}/wes/v1/{namespace}",
        directory / f"{case}.cwl",
        json.loads((directory / f"{case}.inputs.json").read_text()),
        ROOT / "output/integration" / namespace / case,
        expected=json.loads(expected_file.read_text())
        if expected_file.exists()
        else None,
        cancel=case == "cancel",
        timeout=int(os.environ.get("WES_TEST_TIMEOUT", "1800")),
    )
    other = "tenant-b" if namespace == "tenant-a" else "tenant-a"
    with httpx.Client(timeout=30, trust_env=False) as client:
        for suffix in ("", "/status"):
            assert (
                client.get(f"{BASE}/wes/v1/{other}/runs/{run_id}{suffix}").status_code
                == 404
            )
        assert (
            client.post(f"{BASE}/wes/v1/{other}/runs/{run_id}/cancel").status_code
            == 404
        )
        assert client.get(f"{BASE}/wes/v1/not-registered/runs").status_code == 404


def test_water_bodies():
    workflow = os.environ.get("WES_WATER_BODIES_CWL")
    inputs = os.environ.get("WES_WATER_BODIES_INPUTS")
    expected = os.environ.get("WES_WATER_BODIES_EXPECTED")
    if not all([workflow, inputs, expected]):
        pytest.skip(
            "Evaluated water-bodies CWL, inputs and expected outputs have not been supplied"
        )
    runner.execute(
        f"{BASE}/wes/v1/tenant-a",
        Path(workflow),
        json.loads(Path(inputs).read_text()),
        ROOT / "output/integration/tenant-a/water-bodies",
        expected=json.loads(Path(expected).read_text()),
        version=os.environ.get("WES_WATER_BODIES_VERSION", "v1.2"),
        entrypoint=os.environ.get("WES_WATER_BODIES_ENTRYPOINT"),
        timeout=int(os.environ.get("WES_TEST_TIMEOUT", "1800")),
    )
