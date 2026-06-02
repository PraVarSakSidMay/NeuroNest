"""Tests for the local wellness MCP server helpers."""
from datetime import datetime, timezone

import pytest

from mcp_server import (
    build_daily_trends,
    export_clinical_report_data,
    render_clinical_report_html,
    summarize_interactions,
)


SAMPLE_INTERACTIONS = [
    {
        "_id": "i1",
        "session_id": "s1",
        "user_id": "u1",
        "emotion": "sad",
        "stress_level": 70,
        "contradiction_detected": True,
        "eye_contact_ratio": 0.4,
        "head_pose": {"pitch": 12, "yaw": 4, "roll": 0},
        "created_at": "2026-05-30T10:00:00+00:00",
    },
    {
        "_id": "i2",
        "session_id": "s1",
        "user_id": "u1",
        "emotion": "anxious",
        "stress_level": 60,
        "contradiction_detected": False,
        "eye_contact_ratio": 0.6,
        "head_pose": {"pitch": 5, "yaw": 2, "roll": 0},
        "created_at": "2026-05-30T11:00:00+00:00",
    },
    {
        "_id": "i3",
        "session_id": "s2",
        "user_id": "u1",
        "emotion": "sad",
        "stress_level": 30,
        "contradiction_detected": False,
        "eye_contact_ratio": 0.9,
        "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
        "created_at": "2026-05-31T09:00:00+00:00",
    },
]


def test_summarize_interactions_includes_visual_telemetry():
    summary = summarize_interactions(SAMPLE_INTERACTIONS)

    assert summary["session_count"] == 2
    assert summary["interaction_count"] == 3
    assert summary["average_stress"] == 53.333
    assert summary["dominant_emotion"] == "sad"
    assert summary["contradiction_rate"] == 0.333
    assert summary["average_eye_contact"] == 0.633


def test_build_daily_trends_groups_chronologically():
    trends = build_daily_trends(SAMPLE_INTERACTIONS)

    assert [row["date"] for row in trends] == ["2026-05-30", "2026-05-31"]
    assert trends[0]["interactions"] == 2
    assert trends[0]["average_stress"] == 65.0
    assert trends[0]["contradiction_count"] == 1
    assert trends[1]["average_eye_contact"] == 0.9


def test_render_clinical_report_html_is_print_friendly():
    summary = summarize_interactions(SAMPLE_INTERACTIONS)
    trends = build_daily_trends(SAMPLE_INTERACTIONS)
    html = render_clinical_report_html(
        summary,
        trends,
        generated_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )

    assert "NeuroNest Clinical Wellness Report" in html
    assert "Average Stress" in html
    assert "2026-05-30" in html
    assert "@media print" in html


@pytest.mark.asyncio
async def test_export_clinical_report_writes_json(monkeypatch, tmp_path):
    async def fake_summary(last_sessions=50):
        return summarize_interactions(SAMPLE_INTERACTIONS)

    async def fake_trends(days=30):
        return build_daily_trends(SAMPLE_INTERACTIONS)

    monkeypatch.setattr("mcp_server.get_wellness_summary_data", fake_summary)
    monkeypatch.setattr("mcp_server.get_daily_trends_data", fake_trends)

    output = tmp_path / "report.json"
    result = await export_clinical_report_data("json", str(output), days=7)

    assert result["format"] == "json"
    assert output.exists()
    assert '"average_eye_contact": 0.633' in output.read_text(encoding="utf-8")
