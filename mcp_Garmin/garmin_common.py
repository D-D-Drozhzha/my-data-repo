"""Shared Garmin Connect helpers: client, cache, compact summaries, training load (CTL/ATL/TSB)."""

from __future__ import annotations

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from garminconnect import Garmin

TOKENSTORE = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))
CACHE_DIR = Path(os.path.expanduser(os.getenv("GARMIN_CACHE", "~/.garminconnect/cache")))

_client: Garmin | None = None
_client_lock = threading.Lock()


class NotLoggedIn(RuntimeError):
    pass


def get_client() -> Garmin:
    """Return a logged-in Garmin client using saved tokens (never asks for a password)."""
    global _client
    with _client_lock:
        if _client is None:
            g = Garmin()
            try:
                g.login(TOKENSTORE)
            except Exception as e:  # noqa: BLE001
                raise NotLoggedIn(
                    "Нет действующего входа в Garmin Connect. Запустите в Терминале: "
                    "~/.local/bin/uv run --script ~/garmin-mcp/garmin_login.py --force  (ошибка: " + str(e)[:200] + ")"
                ) from e
            _client = g
        return _client


def reset_client() -> None:
    global _client
    with _client_lock:
        _client = None


# ---------------------------------------------------------------- dates

def to_date(s: str | None, default: date | None = None) -> date:
    if not s:
        return default or date.today()
    s = s.strip().lower()
    if s in ("today", "сегодня"):
        return date.today()
    if s in ("yesterday", "вчера"):
        return date.today() - timedelta(days=1)
    return datetime.strptime(s, "%Y-%m-%d").date()


def drange(start: date, end: date) -> list[date]:
    n = (end - start).days
    return [start + timedelta(days=i) for i in range(n + 1)]


# ---------------------------------------------------------------- cache
# Past days (older than yesterday) rarely change, so their per-day payloads are cached on disk.

def cached_day(kind: str, d: date, fetch: Callable[[str], Any]) -> Any:
    ds = d.isoformat()
    cacheable = d < date.today() - timedelta(days=1)
    path = CACHE_DIR / kind / f"{ds}.json"
    if cacheable and path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:  # noqa: BLE001
            pass
    try:
        data = fetch(ds)
    except Exception as e:  # noqa: BLE001
        return {"_error": str(e)[:300]}
    if cacheable and data:
        try:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            path.write_text(json.dumps(data))
        except Exception:  # noqa: BLE001
            pass
    return data


def parallel(fn: Callable[[Any], Any], items: list[Any], workers: int = 4) -> list[Any]:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))


# ---------------------------------------------------------------- helpers

def g(d: Any, *path: Any, default: Any = None) -> Any:
    """Safe nested get: g(x, 'a', 'b', 0, 'c')."""
    cur = d
    for p in path:
        if cur is None:
            return default
        if isinstance(p, int):
            if isinstance(cur, list) and -len(cur) <= p < len(cur):
                cur = cur[p]
            else:
                return default
        elif isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return default
    return default if cur is None else cur


def clean(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != {} and v != []}


def hours(sec: Any) -> float | None:
    return round(sec / 3600, 2) if isinstance(sec, (int, float)) else None


def minutes(sec: Any) -> float | None:
    return round(sec / 60, 1) if isinstance(sec, (int, float)) else None


def pace(speed_mps: Any) -> str | None:
    if not isinstance(speed_mps, (int, float)) or speed_mps <= 0:
        return None
    s = 1000 / speed_mps
    return f"{int(s // 60)}:{int(round(s % 60)):02d}/km"


def first_device_value(d: Any) -> Any:
    """Garmin often nests per-device maps {deviceId: {...}}; return the first value."""
    if isinstance(d, dict) and d:
        return next(iter(d.values()))
    return None


# ---------------------------------------------------------------- compact summaries

def sleep_summary(raw: dict[str, Any]) -> dict[str, Any]:
    s = g(raw, "dailySleepDTO", default={}) or {}
    return clean({
        "date": s.get("calendarDate"),
        "sleep_score": g(s, "sleepScores", "overall", "value"),
        "sleep_quality": g(s, "sleepScores", "overall", "qualifierKey"),
        "total_h": hours(s.get("sleepTimeSeconds")),
        "deep_h": hours(s.get("deepSleepSeconds")),
        "light_h": hours(s.get("lightSleepSeconds")),
        "rem_h": hours(s.get("remSleepSeconds")),
        "awake_h": hours(s.get("awakeSleepSeconds")),
        "awake_count": s.get("awakeCount"),
        "avg_sleep_stress": s.get("avgSleepStress"),
        "avg_respiration": s.get("averageRespirationValue"),
        "avg_spo2": s.get("averageSpO2Value"),
        "resting_hr": raw.get("restingHeartRate"),
        "avg_overnight_hrv": raw.get("avgOvernightHrv"),
        "hrv_status": raw.get("hrvStatus"),
        "body_battery_change": raw.get("bodyBatteryChange"),
        "feedback": g(s, "sleepScoreFeedback"),
        "insight": g(s, "sleepScoreInsight"),
    })


def hrv_summary(raw: dict[str, Any] | None) -> dict[str, Any]:
    h = g(raw, "hrvSummary", default={}) or {}
    return clean({
        "date": h.get("calendarDate"),
        "last_night_avg": h.get("lastNightAvg"),
        "last_night_5min_high": h.get("lastNight5MinHigh"),
        "weekly_avg": h.get("weeklyAvg"),
        "status": h.get("status"),
        "baseline_low": g(h, "baseline", "balancedLow"),
        "baseline_high": g(h, "baseline", "balancedUpper"),
        "feedback": h.get("feedbackPhrase"),
    })


def day_summary(raw: dict[str, Any]) -> dict[str, Any]:
    return clean({
        "date": raw.get("calendarDate"),
        "steps": raw.get("totalSteps"),
        "step_goal": raw.get("dailyStepGoal"),
        "distance_km": round(raw["totalDistanceMeters"] / 1000, 2) if raw.get("totalDistanceMeters") else None,
        "calories_total": raw.get("totalKilocalories"),
        "calories_active": raw.get("activeKilocalories"),
        "floors": raw.get("floorsAscended"),
        "intensity_min_moderate": raw.get("moderateIntensityMinutes"),
        "intensity_min_vigorous": raw.get("vigorousIntensityMinutes"),
        "resting_hr": raw.get("restingHeartRate"),
        "min_hr": raw.get("minHeartRate"),
        "max_hr": raw.get("maxHeartRate"),
        "avg_stress": raw.get("averageStressLevel"),
        "max_stress": raw.get("maxStressLevel"),
        "stress_qualifier": raw.get("stressQualifier"),
        "body_battery_high": raw.get("bodyBatteryHighestValue"),
        "body_battery_low": raw.get("bodyBatteryLowestValue"),
        "body_battery_now": raw.get("bodyBatteryMostRecentValue"),
        "body_battery_charged": raw.get("bodyBatteryChargedValue"),
        "body_battery_drained": raw.get("bodyBatteryDrainedValue"),
        "avg_spo2": raw.get("averageSpo2"),
        "lowest_spo2": raw.get("lowestSpo2"),
        "avg_waking_respiration": raw.get("avgWakingRespirationValue"),
    })


def readiness_summary(raw: Any) -> dict[str, Any]:
    r = raw[0] if isinstance(raw, list) and raw else (raw if isinstance(raw, dict) else {})
    return clean({
        "score": r.get("score"),
        "level": r.get("level"),
        "feedback": r.get("feedbackShort"),
        "feedback_long": r.get("feedbackLong"),
        "sleep_score": r.get("sleepScore"),
        "sleep_factor": r.get("sleepScoreFactorFeedback"),
        "recovery_time_h": round(r["recoveryTime"] / 60, 1) if isinstance(r.get("recoveryTime"), (int, float)) else None,
        "recovery_factor": r.get("recoveryTimeFactorFeedback"),
        "hrv_weekly_avg": r.get("hrvWeeklyAverage"),
        "hrv_factor": r.get("hrvFactorFeedback"),
        "acute_load": r.get("acuteLoad"),
        "acwr_factor": r.get("acwrFactorFeedback"),
        "stress_history_factor": r.get("stressHistoryFactorFeedback"),
        "sleep_history_factor": r.get("sleepHistoryFactorFeedback"),
    })


def training_status_summary(raw: dict[str, Any]) -> dict[str, Any]:
    vo2 = g(raw, "mostRecentVO2Max", "generic", default={}) or {}
    vo2c = g(raw, "mostRecentVO2Max", "cycling", default={}) or {}
    ts = first_device_value(g(raw, "mostRecentTrainingStatus", "latestTrainingStatusData")) or {}
    lb = first_device_value(g(raw, "mostRecentTrainingLoadBalance", "metricsTrainingLoadBalanceDTOMap")) or {}
    acute = ts.get("acuteTrainingLoadDTO") or {}
    return clean({
        "vo2max_running": vo2.get("vo2MaxPreciseValue") or vo2.get("vo2MaxValue"),
        "vo2max_cycling": vo2c.get("vo2MaxPreciseValue") or vo2c.get("vo2MaxValue"),
        "fitness_age": vo2.get("fitnessAge"),
        "training_status": ts.get("trainingStatusFeedbackPhrase") or ts.get("trainingStatus"),
        "load_acute_7d": acute.get("dailyTrainingLoadAcute"),
        "load_chronic_28d": acute.get("dailyTrainingLoadChronic"),
        "acwr_percent": acute.get("acwrPercent"),
        "acwr_status": acute.get("acwrStatus"),
        "load_balance": lb.get("trainingBalanceFeedbackPhrase"),
        "monthly_load_aerobic_low": lb.get("monthlyLoadAerobicLow"),
        "monthly_load_aerobic_high": lb.get("monthlyLoadAerobicHigh"),
        "monthly_load_anaerobic": lb.get("monthlyLoadAnaerobic"),
    })


def activity_row(a: dict[str, Any]) -> dict[str, Any]:
    t = g(a, "activityType", "typeKey")
    dist = a.get("distance")
    zones = [a.get(f"hrTimeInZone_{i}") for i in range(1, 6)]
    return clean({
        "id": a.get("activityId"),
        "name": a.get("activityName"),
        "type": t,
        "start": a.get("startTimeLocal"),
        "duration_min": minutes(a.get("duration")),
        "moving_min": minutes(a.get("movingDuration")),
        "distance_km": round(dist / 1000, 2) if isinstance(dist, (int, float)) and dist > 0 else None,
        "avg_pace": pace(a.get("averageSpeed")) if t and ("run" in t or "walk" in t or "hik" in t) else None,
        "avg_speed_kmh": round(a["averageSpeed"] * 3.6, 1) if isinstance(a.get("averageSpeed"), (int, float)) and a["averageSpeed"] > 0 else None,
        "avg_hr": a.get("averageHR"),
        "max_hr": a.get("maxHR"),
        "calories": a.get("calories"),
        "training_load": round(a["activityTrainingLoad"], 1) if isinstance(a.get("activityTrainingLoad"), (int, float)) else None,
        "aerobic_te": a.get("aerobicTrainingEffect"),
        "anaerobic_te": a.get("anaerobicTrainingEffect"),
        "te_label": a.get("trainingEffectLabel"),
        "elev_gain_m": a.get("elevationGain"),
        "avg_cadence": a.get("averageRunningCadenceInStepsPerMinute") or a.get("averageBikingCadenceInRevPerMinute"),
        "avg_power": a.get("avgPower"),
        "vo2max": a.get("vO2MaxValue"),
        "hr_zones_min": [minutes(z) or 0 for z in zones] if any(zones) else None,
        "steps": a.get("steps"),
    })


def lap_row(l: dict[str, Any]) -> dict[str, Any]:
    dist = l.get("distance")
    return clean({
        "lap": l.get("lapIndex"),
        "intensity": l.get("intensityType"),
        "distance_m": round(dist) if isinstance(dist, (int, float)) else None,
        "duration": f"{int(l['duration'] // 60)}:{int(l['duration'] % 60):02d}" if isinstance(l.get("duration"), (int, float)) else None,
        "pace": pace(l.get("averageSpeed")),
        "avg_hr": l.get("averageHR"),
        "max_hr": l.get("maxHR"),
        "cadence": l.get("averageRunCadence"),
        "power": l.get("averagePower"),
        "elev_gain": l.get("elevationGain"),
    })


# ---------------------------------------------------------------- training load (CTL / ATL / TSB)

def training_load_series(api: Garmin, days: int = 90, warmup: int = 120) -> dict[str, Any]:
    """Performance Management Chart from Garmin per-activity training load.

    CTL ("fitness") = 42-day EWMA of daily load, ATL ("fatigue") = 7-day EWMA,
    TSB ("form") = yesterday's CTL - yesterday's ATL.
    Garmin training load (EPOC-based) is used instead of TrainingPeaks TSS, so absolute
    values differ from TrainingPeaks, but the trends and signs read the same way.
    """
    end = date.today()
    start = end - timedelta(days=days + warmup)
    acts = api.get_activities_by_date(start.isoformat(), end.isoformat()) or []
    daily: dict[str, float] = {}
    for a in acts:
        load = a.get("activityTrainingLoad")
        d = (a.get("startTimeLocal") or "")[:10]
        if d and isinstance(load, (int, float)):
            daily[d] = daily.get(d, 0.0) + float(load)
    ctl = atl = 0.0
    series = []
    for d in drange(start, end):
        ds = d.isoformat()
        tsb = ctl - atl
        load = daily.get(ds, 0.0)
        ctl += (load - ctl) / 42
        atl += (load - atl) / 7
        if d > end - timedelta(days=days):
            series.append({"date": ds, "load": round(load, 1), "ctl": round(ctl, 1),
                           "atl": round(atl, 1), "tsb": round(tsb, 1)})
    return {"series": series, "activities_counted": len(acts)}
