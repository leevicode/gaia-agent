import json

import pytest

from app.bdi_trace_store import (
    append_bdi_traces,
    build_bdi_trace_entry,
    load_bdi_trace_log,
)


def test_build_bdi_trace_entry_filters_empty_traces():
    trace = {
        "agent_name": "RecommendationAgent",
        "selected_plan": "select_legitimate_and_warn",
    }

    entry = build_bdi_trace_entry(
        request_id="req-1",
        scenario="software_deal",
        query="Crimson Desert",
        traces=[
            trace,
            None,
        ],
    )

    assert entry["request_id"] == "req-1"
    assert entry["scenario"] == "software_deal"
    assert entry["query"] == "Crimson Desert"
    assert entry["trace_count"] == 1
    assert entry["traces"] == [trace]


def test_append_bdi_traces_creates_trace_file(tmp_path):
    trace_file = tmp_path / "bdi_trace.json"

    trace = {
        "agent_name": "SoftwareCoordinatorAgent",
        "selected_plan": "query_software_sources",
    }

    append_bdi_traces(
        request_id="req-1",
        scenario="software_deal",
        query="Crimson Desert",
        traces=[trace],
        trace_file=trace_file,
    )

    data = json.loads(trace_file.read_text(encoding="utf-8"))

    assert len(data) == 1
    assert data[0]["request_id"] == "req-1"
    assert data[0]["traces"][0]["agent_name"] == "SoftwareCoordinatorAgent"


def test_append_bdi_traces_appends_without_overwriting(tmp_path):
    trace_file = tmp_path / "bdi_trace.json"

    append_bdi_traces(
        request_id="req-1",
        scenario="software_deal",
        query="Crimson Desert",
        traces=[
            {
                "agent_name": "SoftwareCoordinatorAgent",
                "selected_plan": "query_software_sources",
            }
        ],
        trace_file=trace_file,
    )

    append_bdi_traces(
        request_id="req-2",
        scenario="local_console_search",
        query="PlayStation 5 Digital Edition",
        traces=[
            {
                "agent_name": "LocalCoordinatorAgent",
                "selected_plan": "query_console_sources",
            }
        ],
        trace_file=trace_file,
    )

    data = load_bdi_trace_log(trace_file=trace_file)

    assert len(data) == 2
    assert data[0]["request_id"] == "req-1"
    assert data[1]["request_id"] == "req-2"


def test_load_bdi_trace_log_rejects_non_list_json(tmp_path):
    trace_file = tmp_path / "bdi_trace.json"
    trace_file.write_text(
        json.dumps({"not": "a list"}),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="must contain a JSON list"):
        load_bdi_trace_log(trace_file=trace_file)