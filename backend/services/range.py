"""
Reflection range resolution service for the NeuroNest Reflective Journal.

Provides ``resolve_reflection_range()`` which maps a preset label (or a
custom date pair) to a concrete ``(start_date, end_date)`` window used when
fetching journal entries for AI summary generation.
"""

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

RangePreset = Literal["3d", "5d", "7d", "30d", "custom"]

# ---------------------------------------------------------------------------
# Preset → day-count mapping
# ---------------------------------------------------------------------------

_PRESET_DAYS: dict[str, int] = {
    "3d": 3,
    "5d": 5,
    "7d": 7,
    "30d": 30,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_reflection_range(
    preset: RangePreset,
    custom_start: Optional[datetime] = None,
    custom_end: Optional[datetime] = None,
) -> dict:
    """Resolve a reflection range to concrete start and end datetimes.

    For preset ranges (``'3d'``, ``'5d'``, ``'7d'``, ``'30d'``), the
    ``start_date`` is computed as ``now - N days`` and ``end_date`` is
    ``now`` (UTC).

    For the ``'custom'`` preset, both ``custom_start`` and ``custom_end``
    must be provided.

    Args:
        preset:       One of ``'3d'``, ``'5d'``, ``'7d'``, ``'30d'``,
                      ``'custom'``.
        custom_start: Required when ``preset == 'custom'``.  The inclusive
                      start of the custom range.
        custom_end:   Required when ``preset == 'custom'``.  The inclusive
                      end of the custom range.

    Returns:
        A dict with keys:
        - ``"preset"``     — the original preset string
        - ``"start_date"`` — a :class:`datetime` (UTC-aware for presets)
        - ``"end_date"``   — a :class:`datetime` (UTC-aware for presets)

    Raises:
        ValueError: If ``preset == 'custom'`` and either date is ``None``.
        ValueError: If ``start_date > end_date``.
    """
    if preset == "custom":
        if custom_start is None or custom_end is None:
            raise ValueError("Custom range requires both start and end dates.")
        start_date = custom_start
        end_date = custom_end
    else:
        days = _PRESET_DAYS[preset]
        now = datetime.now(tz=timezone.utc)
        start_date = now - timedelta(days=days)
        end_date = now

    if start_date > end_date:
        raise ValueError("Start date must be before end date.")

    return {
        "preset": preset,
        "start_date": start_date,
        "end_date": end_date,
    }
