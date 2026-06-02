"""Local MCP server for longitudinal wellness telemetry.

Run with:
    python mcp_server.py

The server uses stdio by default so it can be launched by MCP clients such as
Claude Desktop. The helper functions are intentionally plain Python so report
generation and aggregation can be tested without an MCP client.
"""
from __future__ import annotations

import asyncio
import html
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from core.config import settings
from infrastructure.mongodb_client import close_db, get_db, init_db

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _avg(values: list[float]) -> Optional[float]:
    return round(sum(values) / len(values), 3) if values else None


def summarize_interactions(interactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Build high-level wellness statistics from interaction documents."""
    stress_values = [
        float(doc["stress_level"])
        for doc in interactions
        if isinstance(doc.get("stress_level"), (int, float))
    ]
    eye_contact_values = [
        float(doc["eye_contact_ratio"])
        for doc in interactions
        if isinstance(doc.get("eye_contact_ratio"), (int, float))
    ]
    emotions = [str(doc.get("emotion")) for doc in interactions if doc.get("emotion")]
    contradictions = [bool(doc.get("contradiction_detected")) for doc in interactions]
    session_ids = {doc.get("session_id") for doc in interactions if doc.get("session_id")}
    dates = [_parse_datetime(doc.get("created_at")) for doc in interactions]
    dates = [date for date in dates if date is not None]

    dominant_emotion = None
    if emotions:
        dominant_emotion = Counter(emotions).most_common(1)[0][0]

    contradiction_rate = None
    if contradictions:
        contradiction_rate = round(sum(contradictions) / len(contradictions), 3)

    return {
        "session_count": len(session_ids),
        "interaction_count": len(interactions),
        "average_stress": _avg(stress_values),
        "dominant_emotion": dominant_emotion,
        "contradiction_rate": contradiction_rate,
        "average_eye_contact": _avg(eye_contact_values),
        "latest_interaction_at": max(dates).isoformat() if dates else None,
    }


def build_daily_trends(interactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate interaction telemetry into chronological daily trend rows."""
    buckets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "stress": [],
            "eye_contact": [],
            "emotions": [],
            "contradictions": 0,
            "interactions": 0,
        }
    )

    for doc in interactions:
        created_at = _parse_datetime(doc.get("created_at"))
        if not created_at:
            continue
        key = created_at.date().isoformat()
        bucket = buckets[key]
        bucket["interactions"] += 1
        if isinstance(doc.get("stress_level"), (int, float)):
            bucket["stress"].append(float(doc["stress_level"]))
        if isinstance(doc.get("eye_contact_ratio"), (int, float)):
            bucket["eye_contact"].append(float(doc["eye_contact_ratio"]))
        if doc.get("emotion"):
            bucket["emotions"].append(str(doc["emotion"]))
        if doc.get("contradiction_detected"):
            bucket["contradictions"] += 1

    rows = []
    for date_key in sorted(buckets):
        bucket = buckets[date_key]
        dominant_emotion = None
        if bucket["emotions"]:
            dominant_emotion = Counter(bucket["emotions"]).most_common(1)[0][0]
        rows.append(
            {
                "date": date_key,
                "interactions": bucket["interactions"],
                "average_stress": _avg(bucket["stress"]),
                "dominant_emotion": dominant_emotion,
                "average_eye_contact": _avg(bucket["eye_contact"]),
                "contradiction_count": bucket["contradictions"],
            }
        )
    return rows


async def _fetch_recent_interactions(
    user_id: str = DEFAULT_USER_ID,
    last_sessions: int = 20,
    days: Optional[int] = None,
) -> list[dict[str, Any]]:
    db = get_db()
    query: dict[str, Any] = {"user_id": user_id}

    if days is not None:
        since = datetime.now(timezone.utc) - timedelta(days=max(days, 1))
        query["created_at"] = {"$gte": since.isoformat()}
    elif last_sessions > 0:
        session_cursor = (
            db["sessions"]
            .find({"user_id": user_id}, {"_id": 1})
            .sort("started_at", -1)
            .limit(last_sessions)
        )
        session_ids = [doc["_id"] async for doc in session_cursor]
        if session_ids:
            query["session_id"] = {"$in": session_ids}

    cursor = db["interactions"].find(query).sort("created_at", 1)
    return [doc async for doc in cursor]


async def get_wellness_summary_data(last_sessions: int = 20) -> dict[str, Any]:
    interactions = await _fetch_recent_interactions(last_sessions=last_sessions)
    summary = summarize_interactions(interactions)
    summary["last_sessions_requested"] = last_sessions
    return summary


async def get_daily_trends_data(days: int = 30) -> list[dict[str, Any]]:
    interactions = await _fetch_recent_interactions(days=days)
    return build_daily_trends(interactions)


def render_clinical_report_html(
    summary: dict[str, Any],
    trends: list[dict[str, Any]],
    generated_at: Optional[datetime] = None,
) -> str:
    generated_at = generated_at or datetime.now(timezone.utc)
    trend_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['date'])}</td>"
        f"<td>{row['interactions']}</td>"
        f"<td>{row['average_stress'] if row['average_stress'] is not None else 'N/A'}</td>"
        f"<td>{html.escape(str(row['dominant_emotion'] or 'N/A'))}</td>"
        f"<td>{row['average_eye_contact'] if row['average_eye_contact'] is not None else 'N/A'}</td>"
        f"<td>{row['contradiction_count']}</td>"
        "</tr>"
        for row in trends
    )
    if not trend_rows:
        trend_rows = "<tr><td colspan='6'>No telemetry available for this period.</td></tr>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>NeuroNest Clinical Wellness Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #172033; margin: 40px; line-height: 1.5; }}
    h1, h2 {{ color: #24365f; }}
    .meta {{ color: #5f6f89; margin-bottom: 28px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 24px 0; }}
    .metric {{ border: 1px solid #d7deea; border-radius: 8px; padding: 14px; background: #f8fafc; }}
    .label {{ color: #637083; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
    .value {{ font-size: 24px; font-weight: 700; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ border: 1px solid #d7deea; padding: 9px; text-align: left; }}
    th {{ background: #eef3fb; }}
    .note {{ border-left: 4px solid #647aa8; padding-left: 12px; color: #44516a; }}
    @media print {{ body {{ margin: 20px; }} .metric {{ break-inside: avoid; }} }}
  </style>
</head>
<body>
  <h1>NeuroNest Clinical Wellness Report</h1>
  <div class="meta">Generated {html.escape(generated_at.isoformat())}</div>
  <p class="note">This report summarizes user-controlled wellness telemetry for clinical review. It is not a diagnosis and should be interpreted by a qualified professional.</p>
  <h2>Summary</h2>
  <section class="grid">
    <div class="metric"><div class="label">Sessions</div><div class="value">{summary.get('session_count', 0)}</div></div>
    <div class="metric"><div class="label">Interactions</div><div class="value">{summary.get('interaction_count', 0)}</div></div>
    <div class="metric"><div class="label">Average Stress</div><div class="value">{summary.get('average_stress') or 'N/A'}</div></div>
    <div class="metric"><div class="label">Dominant Emotion</div><div class="value">{html.escape(str(summary.get('dominant_emotion') or 'N/A'))}</div></div>
    <div class="metric"><div class="label">Contradiction Rate</div><div class="value">{summary.get('contradiction_rate') if summary.get('contradiction_rate') is not None else 'N/A'}</div></div>
    <div class="metric"><div class="label">Avg Eye Contact</div><div class="value">{summary.get('average_eye_contact') if summary.get('average_eye_contact') is not None else 'N/A'}</div></div>
  </section>
  <h2>Daily Trends</h2>
  <table>
    <thead><tr><th>Date</th><th>Interactions</th><th>Avg Stress</th><th>Dominant Emotion</th><th>Avg Eye Contact</th><th>Contradictions</th></tr></thead>
    <tbody>{trend_rows}</tbody>
  </table>
</body>
</html>"""


async def export_clinical_report_data(
    report_format: str = "html",
    filepath: Optional[str] = None,
    days: int = 30,
) -> dict[str, Any]:
    report_format = report_format.lower().strip()
    if report_format not in {"json", "html"}:
        raise ValueError("format must be either 'json' or 'html'")

    summary = await get_wellness_summary_data(last_sessions=50)
    trends = await get_daily_trends_data(days=days)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "trends": trends,
    }

    if filepath:
        path = Path(filepath)
    else:
        output_dir = Path(getattr(settings, "GENERATED_DIR", "generated") or "generated")
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"clinical_report.{report_format}"

    if report_format == "json":
        content = json.dumps(payload, indent=2, default=str)
    else:
        content = render_clinical_report_html(summary, trends)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"format": report_format, "filepath": str(path), "summary": summary}


async def generate_clinical_summary_data(last_sessions: int = 20) -> dict[str, Any]:
    interactions = await _fetch_recent_interactions(last_sessions=last_sessions)
    summary = summarize_interactions(interactions)
    recent = interactions[-10:]
    timeline = [
        {
            "created_at": doc.get("created_at"),
            "emotion": doc.get("emotion"),
            "stress_level": doc.get("stress_level"),
            "eye_contact_ratio": doc.get("eye_contact_ratio"),
            "contradiction_detected": doc.get("contradiction_detected"),
            "transcript": doc.get("transcript", "")[:240],
        }
        for doc in recent
    ]

    try:
        from services.model_manager import model_manager

        prompt = (
            "Write a concise therapist-facing clinical overview from this "
            "wellness telemetry. Avoid diagnosis. Focus on patterns, changes, "
            "risk flags, strengths, and suggested discussion areas.\n\n"
            f"Summary:\n{json.dumps(summary, indent=2)}\n\n"
            f"Recent timeline:\n{json.dumps(timeline, indent=2)}"
        )
        text = model_manager.get_llm_response("", prompt, json_mode=False)
    except Exception as exc:
        text = (
            "Clinical summary generation was unavailable. "
            f"Telemetry summary: {json.dumps(summary, default=str)}. Error: {exc}"
        )

    return {"summary": text, "metrics": summary, "recent_interactions": timeline}


def build_mcp_server():
    if FastMCP is None:
        raise RuntimeError("The 'mcp' package is required. Install dependencies with pip install -r requirements.txt.")

    server = FastMCP("NeuroNest Wellness")

    @server.resource("wellness://summary")
    async def wellness_summary() -> str:
        return json.dumps(await get_wellness_summary_data(), indent=2, default=str)

    @server.resource("wellness://trends")
    async def wellness_trends() -> str:
        return json.dumps(await get_daily_trends_data(), indent=2, default=str)

    @server.tool()
    async def get_wellness_summary(last_sessions: int = 20) -> dict[str, Any]:
        """Get structured wellness statistics for the last N sessions."""
        return await get_wellness_summary_data(last_sessions=last_sessions)

    @server.tool()
    async def get_daily_trends(days: int = 30) -> list[dict[str, Any]]:
        """Get daily stress, mood, contradiction, and eye-contact trends."""
        return await get_daily_trends_data(days=days)

    @server.tool()
    async def export_clinical_report(
        format: str = "html",
        filepath: Optional[str] = None,
    ) -> dict[str, Any]:
        """Export a clinical telemetry report as json or print-friendly html."""
        return await export_clinical_report_data(report_format=format, filepath=filepath)

    @server.tool()
    async def generate_clinical_summary(last_sessions: int = 20) -> dict[str, Any]:
        """Generate a therapist-facing, non-diagnostic clinical overview."""
        return await generate_clinical_summary_data(last_sessions=last_sessions)

    return server


if __name__ == "__main__":
    asyncio.run(init_db())
    try:
        build_mcp_server().run()
    finally:
        asyncio.run(close_db())
