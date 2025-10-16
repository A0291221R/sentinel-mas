# sentinel_mas/timewin.py
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import Tuple, Optional
import pytz

SGT = pytz.timezone("Asia/Singapore")

# --- date patterns ---
RE_DMY_DASH   = re.compile(r"\b(?P<d>\d{1,2})-(?P<m>\d{1,2})-(?P<y>\d{4})\b")  # 13-10-2025
RE_ISO        = re.compile(r"\b(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})\b")      # 2025-10-13
RE_DMY_SLASH  = re.compile(r"\b(?P<d>\d{1,2})/(?P<m>\d{1,2})/(?P<y>\d{4})\b")  # 13/10/2025
RE_DMY_TEXT   = re.compile(
    r"\b(?P<d>\d{1,2})[-/\s](?P<mon>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[-/\s](?P<y>\d{4})\b",
    re.IGNORECASE
)
MON = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"sept":9,"oct":10,"nov":11,"dec":12}

# --- time tokens ---
# Prefer strict range (has ":" or am/pm or "now"); fallback to pure HH-HH after date removal.
RE_RANGE_STRICT = re.compile(
    r"(?:between\s+)?(?P<t1>now|\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|and|-|–|—)\s*(?P<t2>now|\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
    re.IGNORECASE
)
RE_RANGE_HH     = re.compile(
    r"(?:between\s+)?(?P<t1>\d{1,2})\s*(?:to|and|-|–|—)\s*(?P<t2>\d{1,2})",
    re.IGNORECASE
)
RE_SINGLE_TIME_STRICT = re.compile(
    r"\b(?P<t>(?:\d{1,2}:\d{2}|\d{1,2}\s*(?:am|pm)))\b",
    re.IGNORECASE
)

# --- relative phrases ---
RE_LAST = re.compile(r"\blast\s+(?P<n>\d+)\s*(?P<u>minutes?|mins?|hours?|hrs?)\b", re.IGNORECASE)
RE_TODAY = re.compile(r"\btoday\b", re.IGNORECASE)
RE_YESTERDAY = re.compile(r"\byesterday\b", re.IGNORECASE)
RE_TOMORROW = re.compile(r"\btomorrow\b", re.IGNORECASE)
RE_DAYPART = re.compile(r"\b(this\s+)?(morning|afternoon|evening|tonight|night)\b", re.IGNORECASE)

DAYPART_WINDOWS = {
    "morning":   (6,  0, 12, 0),   # 06:00–12:00
    "afternoon": (12, 0, 18, 0),   # 12:00–18:00
    "evening":   (18, 0, 22, 0),   # 18:00–22:00
    "night":     (22, 0, 6,  0),   # 22:00–06:00 (+1 day)
    "tonight":   (22, 0, 6,  0),   # alias of night
}

def _localize_sgt(y: int, m: int, d: int, hh: int, mm: int) -> datetime:
    return SGT.localize(datetime(y, m, d, hh, mm, 0, 0))

def _now_sgt() -> datetime:
    return datetime.now(SGT)

def _parse_hhmm(tok: str, now: datetime) -> tuple[int, int, bool]:
    """Return (hour_24, minute, is_now_token)."""
    t = tok.strip().lower()
    if t == "now":
        return now.hour, now.minute, True
    ampm = None
    if t.endswith("am") or t.endswith("pm"):
        ampm = t[-2:]
        t = t[:-2].strip()
    if ":" in t:
        h, m = t.split(":", 1)
        hh, mm = int(h), int(m)
    else:
        hh, mm = int(t), 0
    if ampm == "am":
        if hh == 12: hh = 0
    elif ampm == "pm":
        if hh != 12: hh += 12
    return hh, mm, False

def _find_date_match(text: str) -> tuple[Optional[re.Match], Optional[tuple[int,int,int]]]:
    for rx in (RE_DMY_DASH, RE_ISO, RE_DMY_SLASH, RE_DMY_TEXT):
        m = rx.search(text)
        if m:
            if rx is RE_DMY_TEXT:
                y, mo, dd = int(m["y"]), MON[m["mon"].lower()], int(m["d"])
            else:
                y, mo, dd = int(m.group("y")), int(m.group("m")), int(m.group("d"))
            return m, (y, mo, dd)
    return None, None

def _apply_relative_date(text: str, base: datetime) -> datetime:
    """Shift base date for today/yesterday/tomorrow tokens."""
    d = base
    if RE_YESTERDAY.search(text):
        d = d - timedelta(days=1)
    elif RE_TOMORROW.search(text):
        d = d + timedelta(days=1)
    # 'today' keeps base
    return d.replace(hour=0, minute=0, second=0, microsecond=0)

def _format_label(start: datetime, end: datetime) -> str:
    return f"{start.strftime('%Y-%m-%d %H:%M')}–{end.strftime('%H:%M')} SGT"

def resolve_time_window(text: str, base_date: Optional[datetime] = None) -> Tuple[int, int, str]:
    """
    Natural windows:
      - Absolute: 'on 13-10-2025 15:00-18:00', '13-Oct-2025 between 15:00–18:00'
      - Relative: 'today 2–4:30pm', 'yesterday 10–11am', 'tomorrow 09:00–11:00'
      - Durations: 'last 15 minutes', 'last 2 hours'
      - Special: 'this morning/afternoon/evening/tonight', 'now–4pm', '2pm–now'
    Returns: (start_ms, end_ms, 'YYYY-MM-DD HH:MM–HH:MM SGT')
    """
    t_raw = text.strip()
    t = t_raw.replace("—", "-").replace("–", "-")  # normalize dashes
    now = base_date.astimezone(SGT) if (base_date and base_date.tzinfo) else (base_date or _now_sgt())

    # --- 0) "last N minutes/hours"
    m_last = RE_LAST.search(t)
    if m_last:
        n = int(m_last.group("n"))
        unit = m_last.group("u").lower()
        delta = timedelta(minutes=n) if unit.startswith(("m", "min")) else timedelta(hours=n)
        end = now
        start = end - delta
        label = _format_label(start, end)
        return int(start.timestamp()*1000), int(end.timestamp()*1000), label

    # --- 1) Daypart quick windows (today by default, or shifted by 'yesterday'/'tomorrow')
    m_daypart = RE_DAYPART.search(t)
    if m_daypart and not (RE_RANGE_STRICT.search(t) or RE_RANGE_HH.search(t)):
        base_midnight = _apply_relative_date(t, now)
        part = m_daypart.group(2).lower()
        sh, sm, eh, em = DAYPART_WINDOWS[part]
        start = base_midnight if sh == 0 and sm == 0 else base_midnight.replace(hour=sh, minute=sm)
        end = base_midnight.replace(hour=eh, minute=em)
        if part in ("night", "tonight"):  # crosses midnight
            end = end + timedelta(days=1)
        label = _format_label(start, end)
        return int(start.timestamp()*1000), int(end.timestamp()*1000), label

    # --- 2) Absolute date? (we’ll cut it out before searching time ranges)
    m_date, ymd = _find_date_match(t)
    if ymd:
        y, mo, dd = ymd
        date_midnight = _localize_sgt(y, mo, dd, 0, 0)
    else:
        # Relative anchors (today/yesterday/tomorrow), midnight
        date_midnight = _apply_relative_date(t, now)

    # remove explicit date substring so "13-10" doesn't look like a time range
    search_text = t
    if m_date:
        search_text = t[:m_date.start()] + " " + t[m_date.end():]

    # --- 3) Time range
    m_rng = RE_RANGE_STRICT.search(search_text) or RE_RANGE_HH.search(search_text)
    if m_rng:
        h1, m1, n1 = _parse_hhmm(m_rng.group("t1"), now)
        h2, m2, n2 = _parse_hhmm(m_rng.group("t2"), now)
        start = now if n1 else date_midnight.replace(hour=h1, minute=m1)
        end   = now if n2 else date_midnight.replace(hour=h2, minute=m2)
        if end <= start:
            end += timedelta(days=1)  # cross-midnight
        label = _format_label(start, end)
        return int(start.timestamp()*1000), int(end.timestamp()*1000), label

    # --- 4) Single time (1-hour window)
    m_single = RE_SINGLE_TIME_STRICT.search(search_text)
    if m_single:
        hh, mm, is_now = _parse_hhmm(m_single.group("t"), now)
        start = now if is_now else date_midnight.replace(hour=hh, minute=mm)
        end = start + timedelta(hours=1)
        label = _format_label(start, end)
        return int(start.timestamp()*1000), int(end.timestamp()*1000), label

    if ymd:  # we detected an explicit date
        start = date_midnight.replace(hour=0, minute=0)
        end   = date_midnight + timedelta(days=1)  # next midnight
        label = _format_label(start, end)
        return int(start.timestamp()*1000), int(end.timestamp()*1000), label

    # # --- 5) Fallback: 2-hour noon window
    # start = date_midnight.replace(hour=12, minute=0)
    # end   = start + timedelta(hours=2)
    # label = _format_label(start, end)
    # return int(start.timestamp()*1000), int(end.timestamp()*1000), label
    raise ValueError("No time window detected")