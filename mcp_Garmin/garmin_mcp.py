# /// script
# requires-python = ">=3.11"
# dependencies = ["garminconnect>=0.3.20", "mcp>=2.3,<3"]
# ///
"""Garmin MCP server for Claude Desktop.

Reads sleep, HRV, Body Battery, stress, heart rate, training readiness/status, activities
with laps and HR zones, computes CTL/ATL/TSB, creates and schedules workouts, and builds
a local HTML dashboard. Uses tokens saved by garmin_login.py; never handles your password.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, timedelta
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from garmin_common import (
    NotLoggedIn, activity_row, cached_day, clean, day_summary, drange, g, get_client,
    hrv_summary, lap_row, minutes, pace, parallel, readiness_summary, reset_client,
    sleep_summary, to_date, training_load_series, training_status_summary,
)

MAX_CHARS = 60_000
READ = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True)

mcp = MCPServer(
    "garmin",
    instructions=(
        "Personal Garmin Connect data of the user (sleep, HRV, Body Battery, stress, HR, "
        "training readiness/status, VO2max, activities with laps, CTL/ATL/TSB). "
        "For training advice start with get_daily_overview and get_training_load; look at "
        "recent activities before recommending a session. Dates are YYYY-MM-DD in the "
        "user's local time. Ask the user before creating, scheduling or deleting workouts."
    ),
)


def out(data: Any) -> str:
    s = json.dumps(data, ensure_ascii=False, default=str)
    if len(s) > MAX_CHARS:
        s = s[:MAX_CHARS] + ' ... [TRUNCATED: narrow the date range or use a more specific tool]'
    return s


def safe(fn):
    """Turn exceptions into readable tool errors; retry once after re-login on auth errors."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except NotLoggedIn as e:
            return out({"error": str(e)})
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "401" in msg or "uthentic" in msg:
                reset_client()
                try:
                    return fn(*args, **kwargs)
                except Exception as e2:  # noqa: BLE001
                    msg = str(e2)
            return out({"error": f"{type(e).__name__}: {msg[:500]}"})
    return wrapper


# ======================================================================= recovery & health

@mcp.tool(annotations=READ)
@safe
def get_daily_overview(day: str = "today") -> str:
    """Morning snapshot for one day: sleep (score, stages), last-night HRV vs baseline,
    resting HR, Body Battery, stress, steps, training readiness and training status.
    Best first call for "how am I / should I train today". day: YYYY-MM-DD | today | yesterday."""
    api = get_client()
    d = to_date(day).isoformat()
    def tryf(f):
        try:
            return f()
        except Exception as e:  # noqa: BLE001
            return {"_error": str(e)[:200]}
    return out(clean({
        "date": d,
        "sleep": sleep_summary(tryf(lambda: api.get_sleep_data(d)) or {}),
        "hrv": hrv_summary(tryf(lambda: api.get_hrv_data(d))),
        "day": day_summary(tryf(lambda: api.get_user_summary(d)) or {}),
        "training_readiness": readiness_summary(tryf(lambda: api.get_training_readiness(d))),
        "training_status": training_status_summary(tryf(lambda: api.get_training_status(d)) or {}),
    }))


@mcp.tool(annotations=READ)
@safe
def get_sleep(day: str = "today", raw: bool = False) -> str:
    """Sleep for the night ending on `day`: score, duration, deep/light/REM/awake, sleep stress,
    respiration, SpO2, overnight HRV, Garmin feedback. raw=true returns the full Garmin payload
    (large: includes minute-level arrays)."""
    data = get_client().get_sleep_data(to_date(day).isoformat())
    return out(data if raw else sleep_summary(data))


@mcp.tool(annotations=READ)
@safe
def get_trends(days: int = 28, end_day: str = "today") -> str:
    """Day-by-day table for the last `days` days (max 120): sleep score & hours, overnight HRV
    and HRV status, resting HR, Body Battery high/low, avg stress, steps, intensity minutes.
    Use it to spot trends (e.g. HRV dropping, poor sleep streak). Past days are cached locally."""
    api = get_client()
    days = max(1, min(int(days), 120))
    end = to_date(end_day)
    dates = drange(end - timedelta(days=days - 1), end)

    def one(d: date) -> dict[str, Any]:
        s = sleep_summary(cached_day("sleep", d, api.get_sleep_data) or {})
        h = hrv_summary(cached_day("hrv", d, api.get_hrv_data))
        u = day_summary(cached_day("summary", d, api.get_user_summary) or {})
        return clean({
            "date": d.isoformat(),
            "sleep_score": s.get("sleep_score"), "sleep_h": s.get("total_h"),
            "deep_h": s.get("deep_h"), "rem_h": s.get("rem_h"),
            "hrv": h.get("last_night_avg"), "hrv_7d": h.get("weekly_avg"), "hrv_status": h.get("status"),
            "rhr": u.get("resting_hr") or s.get("resting_hr"),
            "bb_high": u.get("body_battery_high"), "bb_low": u.get("body_battery_low"),
            "stress": u.get("avg_stress"), "steps": u.get("steps"),
            "intensity_min": (u.get("intensity_min_moderate") or 0) + 2 * (u.get("intensity_min_vigorous") or 0),
        })
    return out(parallel(one, dates))


@mcp.tool(annotations=READ)
@safe
def get_hrv(start_day: str, end_day: str = "today") -> str:
    """Overnight HRV per day between two dates (≤ 90 days): last-night avg, 7-day avg, status,
    personal baseline range and Garmin feedback."""
    api = get_client()
    a, b = to_date(start_day), to_date(end_day)
    dates = drange(a, b)[-90:]
    return out(parallel(lambda d: hrv_summary(cached_day("hrv", d, api.get_hrv_data)) or {"date": d.isoformat()}, dates))


@mcp.tool(annotations=READ)
@safe
def get_body_battery(start_day: str, end_day: str = "today") -> str:
    """Body Battery per day (charged, drained, high/low) plus intraday events for each day."""
    api = get_client()
    data = api.get_body_battery(to_date(start_day).isoformat(), to_date(end_day).isoformat())
    rows = []
    for d in data or []:
        vals = [v[1] for v in (d.get("bodyBatteryValuesArray") or []) if isinstance(v, list) and len(v) > 1 and v[1] is not None]
        rows.append(clean({
            "date": d.get("date"), "charged": d.get("charged"), "drained": d.get("drained"),
            "high": max(vals) if vals else None, "low": min(vals) if vals else None,
            "events": [clean({"type": e.get("eventType"), "start_gmt": e.get("eventStartTimeGmt"),
                              "duration_min": minutes((e.get("durationInMilliseconds") or 0) / 1000) or None,
                              "impact": e.get("bodyBatteryImpact"), "feedback": e.get("shortFeedback")})
                       for e in (d.get("bodyBatteryActivityEvent") or []) if isinstance(e, dict)],
            "feedback": g(d, "bodyBatteryDynamicFeedbackEvent", "feedbackShortType"),
        }))
    return out(rows)


@mcp.tool(annotations=READ)
@safe
def get_stress(day: str = "today") -> str:
    """Stress for a day: average/max and minutes in rest/low/medium/high stress."""
    api = get_client()
    d = to_date(day).isoformat()
    raw = api.get_stress_data(d) or {}
    u = api.get_user_summary(d) or {}
    return out(clean({
        "date": d, "avg_stress": raw.get("avgStressLevel"), "max_stress": raw.get("maxStressLevel"),
        "rest_min": minutes(u.get("restStressDuration")), "low_min": minutes(u.get("lowStressDuration")),
        "medium_min": minutes(u.get("mediumStressDuration")), "high_min": minutes(u.get("highStressDuration")),
        "qualifier": u.get("stressQualifier"),
    }))


@mcp.tool(annotations=READ)
@safe
def get_heart_rate(day: str = "today", include_intraday: bool = False) -> str:
    """Heart rate for a day: resting, min, max, 7-day average resting HR; optionally the
    intraday series (every ~2 min, large)."""
    raw = get_client().get_heart_rates(to_date(day).isoformat()) or {}
    res = clean({
        "date": raw.get("calendarDate"), "resting_hr": raw.get("restingHeartRate"),
        "min_hr": raw.get("minHeartRate"), "max_hr": raw.get("maxHeartRate"),
        "resting_hr_7d_avg": raw.get("lastSevenDaysAvgRestingHeartRate"),
    })
    if include_intraday:
        res["intraday"] = raw.get("heartRateValues")
    return out(res)


@mcp.tool(annotations=READ)
@safe
def get_daily_activity(start_day: str, end_day: str = "today") -> str:
    """Daily activity per day (≤ 62 days): steps vs goal, distance, calories, floors,
    intensity minutes, resting HR, stress, Body Battery, SpO2, respiration."""
    api = get_client()
    dates = drange(to_date(start_day), to_date(end_day))[-62:]
    return out(parallel(lambda d: day_summary(cached_day("summary", d, api.get_user_summary) or {}) or {"date": d.isoformat()}, dates))


@mcp.tool(annotations=READ)
@safe
def get_training_readiness(day: str = "today") -> str:
    """Training Readiness score and its factors (sleep, recovery time, HRV, acute load,
    stress history) for a day."""
    return out(readiness_summary(get_client().get_training_readiness(to_date(day).isoformat())))


@mcp.tool(annotations=READ)
@safe
def get_training_status(day: str = "today") -> str:
    """Garmin Training Status: status phrase (productive, maintaining, unproductive…), acute
    and chronic load, ACWR, load balance (aerobic low/high/anaerobic), VO2max."""
    return out(training_status_summary(get_client().get_training_status(to_date(day).isoformat()) or {}))


# ======================================================================= training

@mcp.tool(annotations=READ)
@safe
def list_activities(start_day: str = "", end_day: str = "today", activity_type: str = "", limit: int = 30) -> str:
    """Activities (runs, gym, squash, padel, cycling…) newest first with duration, distance,
    pace, HR, training load, aerobic/anaerobic training effect, minutes in HR zones 1-5.
    start_day defaults to 30 days ago. activity_type examples: running, cycling, walking,
    strength_training, fitness_equipment, other."""
    api = get_client()
    end = to_date(end_day)
    start = to_date(start_day, end - timedelta(days=30))
    acts = api.get_activities_by_date(start.isoformat(), end.isoformat(), activity_type or None) or []
    return out([activity_row(a) for a in acts[: max(1, min(int(limit), 200))]])


@mcp.tool(annotations=READ)
@safe
def get_activity(activity_id: str, include_laps: bool = True, include_hr_zones: bool = True) -> str:
    """One activity in detail: summary, laps/splits (pace, HR, cadence, power per lap — use for
    interval analysis), time in HR zones, weather."""
    api = get_client()
    a = api.get_activity(activity_id) or {}
    s = a.get("summaryDTO") or {}
    flat = {**s, "activityId": a.get("activityId"), "activityName": a.get("activityName"),
            "activityType": a.get("activityTypeDTO"), "startTimeLocal": s.get("startTimeLocal")}
    res: dict[str, Any] = {"summary": activity_row(flat)}
    res["summary"].update(clean({
        "description": a.get("description"),
        "training_effect_message": s.get("aerobicTrainingEffectMessage"),
        "recovery_hr": s.get("recoveryHeartRate"),
        "body_battery_impact": s.get("differenceBodyBattery"),
        "avg_stride_m": s.get("strideLength") and round(s["strideLength"] / 100, 2),
        "ground_contact_ms": s.get("groundContactTime"),
        "vertical_oscillation_cm": s.get("verticalOscillation"),
        "sweat_loss_ml": s.get("waterEstimated"),
    }))
    if include_laps:
        try:
            laps = (api.get_activity_splits(activity_id) or {}).get("lapDTOs") or []
            res["laps"] = [lap_row(l) for l in laps]
        except Exception as e:  # noqa: BLE001
            res["laps_error"] = str(e)[:200]
    if include_hr_zones:
        try:
            z = api.get_activity_hr_in_timezones(activity_id) or []
            res["hr_zones"] = [clean({"zone": x.get("zoneNumber"), "from_bpm": x.get("zoneLowBoundary"),
                                      "minutes": minutes(x.get("secsInZone"))}) for x in z]
        except Exception as e:  # noqa: BLE001
            res["hr_zones_error"] = str(e)[:200]
    try:
        w = api.get_activity_weather(activity_id) or {}
        res["weather"] = clean({"temp_c": w.get("temp") and round((w["temp"] - 32) * 5 / 9, 1),
                                "humidity": w.get("relativeHumidity"), "desc": g(w, "weatherTypeDTO", "desc")})
    except Exception:  # noqa: BLE001
        pass
    return out(res)


@mcp.tool(annotations=READ)
@safe
def get_training_load(days: int = 42) -> str:
    """Fitness / fatigue / form (Performance Management Chart) from Garmin training load:
    CTL = 42-day load average ("fitness"), ATL = 7-day ("fatigue"), TSB = CTL - ATL ("form";
    below about -20 = heavy fatigue, -10…+5 = productive, above +15 = fresh/detraining).
    Note: based on Garmin EPOC load, not TrainingPeaks TSS, so read trends rather than absolute values."""
    days = max(7, min(int(days), 365))
    res = training_load_series(get_client(), days=days)
    cur = res["series"][-1] if res["series"] else {}
    week_ago = res["series"][-8] if len(res["series"]) >= 8 else {}
    return out({"today": cur, "week_ago": week_ago, "series": res["series"]})


@mcp.tool(annotations=READ)
@safe
def get_performance_metrics() -> str:
    """VO2max, race predictions (5K/10K/half/marathon), endurance score, hill score, fitness
    age, lactate threshold, heart-rate zones."""
    api = get_client()
    d = date.today().isoformat()
    res: dict[str, Any] = {}
    calls = {
        "max_metrics": lambda: api.get_max_metrics(d),
        "race_predictions": lambda: api.get_race_predictions(),
        "endurance_score": lambda: api.get_endurance_score(d),
        "hill_score": lambda: api.get_hill_score(d),
        "fitness_age": lambda: api.get_fitnessage_data(d),
        "lactate_threshold": lambda: api.get_lactate_threshold(),
        "heart_rate_zones": lambda: api.get_heart_rate_zones(),
    }
    for k, f in calls.items():
        try:
            res[k] = f()
        except Exception as e:  # noqa: BLE001
            res[k] = {"_error": str(e)[:150]}
    rp = res.get("race_predictions")
    if isinstance(rp, dict):
        def t(sec):
            return f"{int(sec // 3600)}:{int(sec % 3600 // 60):02d}:{int(sec % 60):02d}" if isinstance(sec, (int, float)) else None
        res["race_predictions"] = clean({"5k": t(rp.get("time5K")), "10k": t(rp.get("time10K")),
                                         "half": t(rp.get("timeHalfMarathon")), "marathon": t(rp.get("timeMarathon"))})
    return out(res)


@mcp.tool(annotations=READ)
@safe
def get_personal_records() -> str:
    """Personal records (fastest 1K/5K/10K, longest run, most steps, etc.)."""
    return out(get_client().get_personal_record())


@mcp.tool(annotations=READ)
@safe
def get_devices() -> str:
    """Garmin devices on the account (model, firmware, last sync)."""
    api = get_client()
    devs = api.get_devices() or []
    res = [clean({"id": d.get("deviceId"), "name": d.get("displayName") or d.get("productDisplayName"),
                  "model": d.get("partNumber"), "firmware": d.get("currentFirmwareVersion"),
                  "last_sync": d.get("lastSyncTime")}) for d in devs]
    try:
        last = api.get_device_last_used() or {}
        res.append({"last_used": clean({"id": last.get("userDeviceId"), "name": last.get("lastUsedDeviceName"),
                                        "upload_time": last.get("lastUsedDeviceUploadTime")})})
    except Exception:  # noqa: BLE001
        pass
    return out(res)


# ======================================================================= workouts (write)

SPORTS = {"running": 1, "cycling": 2, "other": 3, "cardio_training": 6, "hiit": 9, "walking": 1}
STEP_TYPES = {"warmup": (1, 1), "cooldown": (2, 2), "interval": (3, 3), "recovery": (4, 4), "rest": (5, 5)}


def _pace_to_mps(p: str) -> float:
    m, s = p.strip().split(":")
    return 1000 / (int(m) * 60 + int(s))


def _build_step(st: dict[str, Any], order: list[int]) -> dict[str, Any]:
    order[0] += 1
    kind = st.get("type", "interval").lower()
    if kind == "repeat":
        my_order = order[0]
        children = [_build_step(c, order) for c in st.get("steps", [])]
        n = int(st.get("iterations", 1))
        return {"type": "RepeatGroupDTO", "stepOrder": my_order,
                "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
                "numberOfIterations": n, "smartRepeat": False, "workoutSteps": children,
                "endCondition": {"conditionTypeId": 7, "conditionTypeKey": "iterations", "displayOrder": 7, "displayable": False},
                "endConditionValue": float(n)}
    tid, disp = STEP_TYPES.get(kind, (3, 3))
    step: dict[str, Any] = {"type": "ExecutableStepDTO", "stepOrder": order[0],
                            "stepType": {"stepTypeId": tid, "stepTypeKey": kind if kind in STEP_TYPES else "interval", "displayOrder": disp}}
    if st.get("description"):
        step["description"] = st["description"]
    if st.get("duration_sec"):
        step["endCondition"] = {"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True}
        step["endConditionValue"] = float(st["duration_sec"])
    elif st.get("distance_m"):
        step["endCondition"] = {"conditionTypeId": 3, "conditionTypeKey": "distance", "displayOrder": 3, "displayable": True}
        step["endConditionValue"] = float(st["distance_m"])
    else:
        step["endCondition"] = {"conditionTypeId": 1, "conditionTypeKey": "lap.button", "displayOrder": 1, "displayable": True}
    no_target = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1}
    if st.get("pace_slow") and st.get("pace_fast"):
        step["targetType"] = {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone", "displayOrder": 6}
        step["targetValueOne"] = _pace_to_mps(st["pace_slow"])
        step["targetValueTwo"] = _pace_to_mps(st["pace_fast"])
    elif st.get("hr_zone"):
        step["targetType"] = {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone", "displayOrder": 4}
        step["zoneNumber"] = int(st["hr_zone"])
    elif st.get("hr_low") and st.get("hr_high"):
        step["targetType"] = {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone", "displayOrder": 4}
        step["targetValueOne"] = float(st["hr_low"])
        step["targetValueTwo"] = float(st["hr_high"])
    else:
        step["targetType"] = no_target
    return step


def _estimate(steps: list[dict[str, Any]]) -> int:
    tot = 0
    for st in steps:
        if st.get("type") == "repeat":
            tot += int(st.get("iterations", 1)) * _estimate(st.get("steps", []))
        elif st.get("duration_sec"):
            tot += int(st["duration_sec"])
        elif st.get("distance_m"):
            tot += int(float(st["distance_m"]) / 1000 * 360)
    return tot


@mcp.tool(annotations=WRITE)
@safe
def create_workout(name: str, steps: list[dict[str, Any]], sport: str = "running",
                   description: str = "", schedule_date: str = "", send_to_watch: bool = False) -> str:
    """Create a structured workout in Garmin Connect (it syncs to the watch), optionally put it
    on the calendar (schedule_date YYYY-MM-DD) and push it to the watch right away.
    Confirm the plan with the user before calling.

    sport: running | cycling | cardio_training | hiit | other.
    steps: list of step objects, in order. Each step:
      {"type": "warmup"|"interval"|"recovery"|"rest"|"cooldown",
       one of "duration_sec": 600 | "distance_m": 1000 | neither (= until lap button),
       optional target: "pace_slow": "5:40", "pace_fast": "5:20" (min:sec per km)
                     | "hr_zone": 2 | "hr_low": 140, "hr_high": 155,
       optional "description": "..."}
    Repeats: {"type": "repeat", "iterations": 5, "steps": [ ...steps... ]}
    Example 5x1km: [{"type":"warmup","duration_sec":600,"hr_zone":2},
      {"type":"repeat","iterations":5,"steps":[{"type":"interval","distance_m":1000,"pace_slow":"5:00","pace_fast":"4:45"},
      {"type":"recovery","duration_sec":120}]},{"type":"cooldown","duration_sec":600}]"""
    api = get_client()
    sid = SPORTS.get(sport.lower(), 3)
    sport_type = {"sportTypeId": sid, "sportTypeKey": sport.lower() if sport.lower() in SPORTS else "other", "displayOrder": 1}
    order = [0]
    workout = {"workoutName": name, "description": description or None, "sportType": sport_type,
               "estimatedDurationInSecs": _estimate(steps),
               "workoutSegments": [{"segmentOrder": 1, "sportType": sport_type,
                                    "workoutSteps": [_build_step(s, order) for s in steps]}]}
    workout = {k: v for k, v in workout.items() if v is not None}
    created = api.upload_workout(workout)
    wid = created.get("workoutId") if isinstance(created, dict) else None
    res: dict[str, Any] = {"created": True, "workout_id": wid, "name": name,
                           "estimated_min": round(workout["estimatedDurationInSecs"] / 60)}
    if wid and schedule_date:
        api.schedule_workout(wid, to_date(schedule_date).isoformat())
        res["scheduled_for"] = to_date(schedule_date).isoformat()
    if wid and send_to_watch:
        try:
            api.push_workout_to_device(wid)
            res["sent_to_watch"] = True
        except Exception as e:  # noqa: BLE001
            res["sent_to_watch_error"] = str(e)[:200]
    return out(res)


@mcp.tool(annotations=READ)
@safe
def list_workouts(limit: int = 30) -> str:
    """Saved workouts in the Garmin Connect library."""
    ws = get_client().get_workouts(0, max(1, min(int(limit), 100))) or []
    return out([clean({"id": w.get("workoutId"), "name": w.get("workoutName"),
                       "sport": g(w, "sportType", "sportTypeKey"), "updated": w.get("updatedDate"),
                       "est_min": w.get("estimatedDurationInSecs") and round(w["estimatedDurationInSecs"] / 60)})
                for w in ws])


@mcp.tool(annotations=READ)
@safe
def get_calendar(start_day: str = "today", end_day: str = "") -> str:
    """Planned workouts / training-plan items on the Garmin calendar (default: next 14 days)."""
    api = get_client()
    a = to_date(start_day)
    b = to_date(end_day, a + timedelta(days=14))
    items = api.get_scheduled_workouts_by_period(a.isoformat(), b.isoformat())
    return out(items)


@mcp.tool(annotations=WRITE)
@safe
def schedule_workout(workout_id: str, day: str) -> str:
    """Put an existing workout from the library on the calendar for a date (YYYY-MM-DD)."""
    return out(get_client().schedule_workout(workout_id, to_date(day).isoformat()))


@mcp.tool(annotations=DESTRUCTIVE)
@safe
def delete_workout(workout_id: str) -> str:
    """Delete a workout from the Garmin Connect library. Only after explicit user confirmation."""
    get_client().delete_workout(workout_id)
    return out({"deleted": workout_id})


# ======================================================================= everything else

@mcp.tool(annotations=READ)
@safe
def list_garmin_methods(filter: str = "") -> str:
    """List all read-only Garmin Connect methods available through call_garmin_method
    (nutrition, menstrual cycle, ECG, SpO2, respiration, weight, gear, badges, race calendar…)."""
    import inspect
    api_cls = type(get_client())
    names = sorted(n for n in dir(api_cls) if n.startswith(("get_", "count_", "search_")) and filter.lower() in n.lower())
    res = []
    for n in names:
        try:
            res.append(f"{n}{inspect.signature(getattr(api_cls, n))}".replace("self, ", "").replace("(self)", "()"))
        except (TypeError, ValueError):
            res.append(n)
    return out(res)


@mcp.tool(annotations=READ)
@safe
def call_garmin_method(method: str, args: dict[str, Any] | None = None) -> str:
    """Call any read-only Garmin Connect method by name (see list_garmin_methods), e.g.
    method="get_spo2_data", args={"cdate": "2026-11-25"}. Only get_*/count_*/search_* allowed.
    Returns the raw Garmin JSON (may be large)."""
    if not method.startswith(("get_", "count_", "search_")):
        return out({"error": "Only read-only methods (get_*, count_*, search_*) are allowed."})
    fn = getattr(get_client(), method, None)
    if not callable(fn):
        return out({"error": f"Unknown method {method}"})
    return out(fn(**(args or {})))


@mcp.tool(annotations=WRITE)
@safe
def build_dashboard(days: int = 30, open_in_browser: bool = True) -> str:
    """Rebuild the local HTML dashboard (sleep, HRV, resting HR, Body Battery, stress, steps,
    CTL/ATL/TSB, recent activities) for the last `days` days and open it in the browser.
    The file stays on this computer (garmin-mcp/dashboard.html)."""
    from garmin_dashboard import build
    path = build(get_client(), days=max(7, min(int(days), 120)))
    if open_in_browser and sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    return out({"dashboard": str(path)})


if __name__ == "__main__":
    mcp.run()
