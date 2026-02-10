"""tools/usage_time_regression.py

Compute session usage durations from `metrics_log.jsonl` and train a
LinearRegression model to predict session duration (minutes) from simple
request-level features.

Outputs:
- tools/usage_time_sessions.csv  : per-session feature dataset
- tools/usage_time_model.joblib  : trained LinearRegression model

Usage:
    python tools/usage_time_regression.py [--metrics-file PATH] [--session-gap-minutes N]

"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import argparse


DEFAULT_METRICS = Path("metrics_log.jsonl")
OUT_DATA = Path("tools") / "usage_time_sessions.csv"
OUT_MODEL = Path("tools") / "usage_time_model.joblib"


def load_metrics(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def build_sessions(events: List[Dict[str, Any]], session_gap_minutes: int = 30) -> List[Dict[str, Any]]:
    # Filter events with user
    evs = [e for e in events if e.get("user")]
    # parse time
    for e in evs:
        e["_dt"] = datetime.fromisoformat(e["time"])
    evs.sort(key=lambda x: (x.get("user"), x["_dt"]))

    sessions = []
    gap = timedelta(minutes=session_gap_minutes)

    from collections import defaultdict
    user_groups = defaultdict(list)
    for e in evs:
        user_groups[e.get("user")].append(e)

    for user, items in user_groups.items():
        sess_start = None
        sess_events = []
        last_ts = None
        for e in items:
            t = e["_dt"]
            if last_ts is None:
                sess_start = t
                sess_events = [e]
                last_ts = t
                continue
            if t - last_ts > gap:
                # close session
                sessions.append(make_session_record(user, sess_start, last_ts, sess_events))
                sess_start = t
                sess_events = [e]
            else:
                sess_events.append(e)
            last_ts = t
        if sess_start is not None and sess_events:
            sessions.append(make_session_record(user, sess_start, last_ts, sess_events))
    return sessions


def make_session_record(user: str, start: datetime, end: datetime, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    dur_min = max(0.0, (end - start).total_seconds() / 60.0)
    latencies = [float(e.get("latency_ms", 0.0)) for e in events]
    endpoints = [e.get("endpoint") for e in events]
    successes = [bool(e.get("success", True)) for e in events]
    record = {
        "user": user,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "duration_min": dur_min,
        "num_requests": len(events),
        "mean_latency_ms": float(np.mean(latencies)) if latencies else 0.0,
        "median_latency_ms": float(np.median(latencies)) if latencies else 0.0,
        "std_latency_ms": float(np.std(latencies)) if latencies else 0.0,
        "error_rate": float(1.0 - sum(1 for s in successes if s) / len(successes)) if successes else 0.0,
        "unique_endpoints": len(set(endpoints)),
        "start_hour": start.hour,
        "day_of_week": start.weekday(),
    }
    return record


def train_and_evaluate(df: pd.DataFrame):
    # drop sessions with zero duration (instantaneous)
    df = df[df["duration_min"] > 0.0].copy()
    if df.shape[0] < 10:
        print("Not enough sessions to train model (need >=10). Found:", df.shape[0])
        return None

    feature_cols = [
        "num_requests",
        "mean_latency_ms",
        "median_latency_ms",
        "std_latency_ms",
        "error_rate",
        "unique_endpoints",
        "start_hour",
        "day_of_week",
    ]
    X = df[feature_cols].astype(float)
    y = df["duration_min"].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    r2 = r2_score(y_test, y_pred)

    print("LinearRegression model trained")
    print(f"Train samples: {X_train.shape[0]}  Test samples: {X_test.shape[0]}")
    print(f"RMSE (min): {rmse:.4f}  R2: {r2:.4f}")

    coefs = dict(zip(feature_cols, model.coef_.tolist()))
    print("Coefficients:")
    for k, v in coefs.items():
        print(f"  {k}: {v:.6f}")

    return model


def main(metrics_file: Path, session_gap_minutes: int = 30):
    if not metrics_file.exists():
        print(f"Metrics file not found: {metrics_file}")
        return
    events = load_metrics(metrics_file)
    print(f"Loaded {len(events)} metric events from {metrics_file}")

    sessions = build_sessions(events, session_gap_minutes=session_gap_minutes)
    print(f"Built {len(sessions)} sessions (gap {session_gap_minutes} minutes)")

    df = pd.DataFrame(sessions)
    OUT_DATA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DATA, index=False)
    print(f"Wrote session dataset to {OUT_DATA}")

    model = train_and_evaluate(df)
    if model is not None:
        joblib.dump(model, OUT_MODEL)
        print(f"Saved trained model to {OUT_MODEL}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-file", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--session-gap-minutes", type=int, default=30)
    args = parser.parse_args()
    main(args.metrics_file, args.session_gap_minutes)
