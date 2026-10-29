import re
from datetime import date, datetime, time, timedelta

from polar import api as polar_api
from polar import db

HISTORY_DAYS = 28
HR_CHUNK_DAYS = 7


def night_series(day, sleep_start_time, samples):
    anchor = datetime.fromisoformat(sleep_start_time).replace(tzinfo=None)
    rows = []
    for hhmm, value in samples.items():
        moment = datetime.combine(anchor.date(), time.fromisoformat(hhmm))
        if moment < anchor - timedelta(hours=1):
            moment += timedelta(days=1)
        rows.append((day, moment.isoformat(timespec="minutes"), value))
    return rows


def duration_seconds(text):
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?", text or "")
    if not match:
        return None
    hours, minutes, seconds = (float(group or 0) for group in match.groups())
    return int(hours * 3600 + minutes * 60 + seconds)


def sync_sleep(conn):
    nights = (polar_api.get("/v3/users/sleep") or {}).get("nights", [])
    starts = {}
    with conn:
        for night in nights:
            day = night["date"]
            start = night["sleep_start_time"]
            starts[day] = start
            db.upsert(conn, "sleep", db.pick(conn, "sleep", night))
            db.replace_series(
                conn, "sleep_hypnogram", day,
                night_series(day, start, night.get("hypnogram", {})),
            )
            db.replace_series(
                conn, "sleep_heart_rate", day,
                night_series(day, start, night.get("heart_rate_samples", {})),
            )
    print(f"sono: {len(nights)} noites")
    return starts


def sync_recharge(conn, sleep_starts):
    recharges = (polar_api.get("/v3/users/nightly-recharge") or {}).get("recharges", [])
    with conn:
        for recharge in recharges:
            day = recharge["date"]
            db.upsert(conn, "nightly_recharge", db.pick(conn, "nightly_recharge", recharge))
            start = sleep_starts.get(day)
            if start is None:
                print(f"  {day}: sem sono correspondente, amostras ignoradas")
                continue
            db.replace_series(
                conn, "recharge_hrv", day,
                night_series(day, start, recharge.get("hrv_samples", {})),
            )
            db.replace_series(
                conn, "recharge_breathing", day,
                night_series(day, start, recharge.get("breathing_samples", {})),
            )
    print(f"nightly recharge: {len(recharges)} noites")


def sync_activities(conn):
    activities = polar_api.get("/v3/users/activities") or []
    with conn:
        for activity in activities:
            activity["date"] = activity["start_time"][:10]
            activity["active_duration_s"] = duration_seconds(activity.get("active_duration"))
            activity["inactive_duration_s"] = duration_seconds(activity.get("inactive_duration"))
            db.upsert(conn, "daily_activity", db.pick(conn, "daily_activity", activity))
    print(f"atividade: {len(activities)} dias")


def sync_continuous_hr(conn):
    end = date.today()
    start = end - timedelta(days=HISTORY_DAYS - 1)
    total_days = 0
    while start <= end:
        chunk_end = min(start + timedelta(days=HR_CHUNK_DAYS - 1), end)
        data = polar_api.get(
            "/v3/users/continuous-heart-rate",
            {"from": str(start), "to": str(chunk_end)},
        ) or {}
        with conn:
            for day_data in data.get("heart_rates", []):
                day = day_data["date"]
                rows = [
                    (day, f"{day}T{sample['sample_time']}", sample["heart_rate"])
                    for sample in day_data.get("heart_rate_samples", [])
                ]
                db.replace_series(conn, "heart_rate", day, rows)
                total_days += 1
        start = chunk_end + timedelta(days=1)
    print(f"fc contínua: {total_days} dias")


def main():
    conn = db.connect()
    sleep_starts = sync_sleep(conn)
    sync_recharge(conn, sleep_starts)
    sync_activities(conn)
    sync_continuous_hr(conn)
    conn.close()


if __name__ == "__main__":
    main()
