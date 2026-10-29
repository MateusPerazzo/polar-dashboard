import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "data" / "polar.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sleep (
    date TEXT PRIMARY KEY,
    sleep_start_time TEXT,
    sleep_end_time TEXT,
    continuity REAL,
    continuity_class INTEGER,
    light_sleep INTEGER,
    deep_sleep INTEGER,
    rem_sleep INTEGER,
    unrecognized_sleep_stage INTEGER,
    sleep_score INTEGER,
    total_interruption_duration INTEGER,
    short_interruption_duration INTEGER,
    long_interruption_duration INTEGER,
    sleep_charge INTEGER,
    sleep_rating INTEGER,
    sleep_goal INTEGER,
    group_duration_score REAL,
    group_solidity_score REAL,
    group_regeneration_score REAL,
    sleep_cycles INTEGER
);

CREATE TABLE IF NOT EXISTS sleep_hypnogram (
    date TEXT,
    timestamp TEXT,
    stage INTEGER,
    PRIMARY KEY (date, timestamp)
);

CREATE TABLE IF NOT EXISTS sleep_heart_rate (
    date TEXT,
    timestamp TEXT,
    heart_rate INTEGER,
    PRIMARY KEY (date, timestamp)
);

CREATE TABLE IF NOT EXISTS nightly_recharge (
    date TEXT PRIMARY KEY,
    heart_rate_avg INTEGER,
    beat_to_beat_avg INTEGER,
    heart_rate_variability_avg INTEGER,
    breathing_rate_avg REAL,
    nightly_recharge_status INTEGER,
    ans_charge REAL,
    ans_charge_status INTEGER
);

CREATE TABLE IF NOT EXISTS recharge_hrv (
    date TEXT,
    timestamp TEXT,
    hrv INTEGER,
    PRIMARY KEY (date, timestamp)
);

CREATE TABLE IF NOT EXISTS recharge_breathing (
    date TEXT,
    timestamp TEXT,
    breathing_rate REAL,
    PRIMARY KEY (date, timestamp)
);

CREATE TABLE IF NOT EXISTS daily_activity (
    date TEXT PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    active_duration_s INTEGER,
    inactive_duration_s INTEGER,
    daily_activity REAL,
    calories INTEGER,
    active_calories INTEGER,
    steps INTEGER,
    inactivity_alert_count INTEGER,
    distance_from_steps REAL
);

CREATE TABLE IF NOT EXISTS heart_rate (
    date TEXT,
    timestamp TEXT,
    heart_rate INTEGER,
    PRIMARY KEY (date, timestamp)
);
"""


def connect():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.executescript(SCHEMA)
    return conn


def columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def pick(conn, table, item):
    return {column: item.get(column) for column in columns(conn, table)}


def upsert(conn, table, row, key="date"):
    names = list(row)
    placeholders = ", ".join("?" for _ in names)
    updates = ", ".join(f"{name} = excluded.{name}" for name in names if name != key)
    sql = (
        f"INSERT INTO {table} ({', '.join(names)}) VALUES ({placeholders}) "
        f"ON CONFLICT({key}) DO UPDATE SET {updates}"
    )
    conn.execute(sql, [row[name] for name in names])


def replace_series(conn, table, day, rows):
    conn.execute(f"DELETE FROM {table} WHERE date = ?", (day,))
    conn.executemany(f"INSERT INTO {table} VALUES (?, ?, ?)", rows)
