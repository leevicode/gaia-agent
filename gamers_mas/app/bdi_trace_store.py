import json
from pathlib import Path
from typing import Any


TRACE_FILE = Path("bdi_trace.json")


def load_bdi_trace_log(trace_file: Path = TRACE_FILE) -> list[dict[str, Any]]:
    if not trace_file.exists():
        return []

    try:
        data = json.loads(trace_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {trace_file}: {exc}") from exc

    if not isinstance(data, list):
        raise RuntimeError(f"{trace_file} must contain a JSON list.")

    return data


def save_bdi_trace_log(
    entries: list[dict[str, Any]],
    trace_file: Path = TRACE_FILE,
) -> None:
    trace_file.write_text(
        json.dumps(entries, indent=2),
        encoding="utf-8",
    )


def build_bdi_trace_entry(
    request_id: str | None,
    scenario: str,
    query: str | None,
    traces: list[dict[str, Any] | None],
) -> dict[str, Any]:
    valid_traces = [
        trace for trace in traces
        if isinstance(trace, dict)
    ]

    return {
        "request_id": request_id,
        "scenario": scenario,
        "query": query,
        "trace_count": len(valid_traces),
        "traces": valid_traces,
    }


def append_bdi_trace_entry(
    entry: dict[str, Any],
    trace_file: Path = TRACE_FILE,
) -> None:
    entries = load_bdi_trace_log(trace_file=trace_file)
    entries.append(entry)
    save_bdi_trace_log(entries, trace_file=trace_file)


def append_bdi_traces(
    request_id: str | None,
    scenario: str,
    query: str | None,
    traces: list[dict[str, Any] | None],
    trace_file: Path = TRACE_FILE,
) -> dict[str, Any]:
    entry = build_bdi_trace_entry(
        request_id=request_id,
        scenario=scenario,
        query=query,
        traces=traces,
    )

    append_bdi_trace_entry(
        entry=entry,
        trace_file=trace_file,
    )

    return entry