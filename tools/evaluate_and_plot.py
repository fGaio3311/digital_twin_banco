"""Evaluate trained usage-time model over sessions and plot predictions vs actuals.

This script can optionally simulate test user activity and append it to
`metrics_log.jsonl` before evaluation.

Usage:
    python tools/evaluate_and_plot.py [--metrics-file PATH] [--model PATH] [--simulate]

Outputs:
- tools/usage_time_predictions.csv
- tools/usage_time_predictions.png

"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import json
import random

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from usage_time_regression import load_metrics, build_sessions

DEFAULT_METRICS = Path("metrics_log.jsonl")
DEFAULT_MODEL = Path("tools") / "usage_time_model.joblib"
OUT_CSV = Path("tools") / "usage_time_predictions.csv"
OUT_PNG = Path("tools") / "usage_time_predictions.png"


def simulate_activity(metrics_file: Path, users: list[str] = None, days: int = 1):
    users = users or ["sim_user1", "sim_user2", "sim_user3"]
    now = datetime.utcnow()
    events = []
    for u in users:
        # create a few sessions per user
        for s in range(3):
            start = now - timedelta(hours=random.randint(0, 48), minutes=random.randint(0, 59))
            n = random.randint(3, 30)
            for i in range(n):
                ts = (start + timedelta(seconds=i * random.randint(1, 120))).isoformat()
                ev = {
                    "time": ts,
                    "endpoint": random.choice(["/balance", "/deposit", "/pix", "/logs", "/register"]),
                    "latency_ms": max(0.5, random.gauss(5.0, 2.0)),
                    "success": random.random() > 0.05,
                    "user": u,
                }
                events.append(ev)
    # append to metrics file
    with metrics_file.open("a", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, default=str) + "\n")
    print(f"Simulated {len(events)} events for users: {', '.join(users)}")


def evaluate(metrics_file: Path, model_file: Path):
    if not metrics_file.exists():
        raise FileNotFoundError(metrics_file)
    if not model_file.exists():
        raise FileNotFoundError(model_file)

    events = load_metrics(metrics_file)
    sessions = build_sessions(events, session_gap_minutes=30)
    df = pd.DataFrame(sessions)
    df = df[df["duration_min"] > 0.0].copy()
    if df.empty:
        print("No sessions to evaluate")
        return

    model = joblib.load(model_file)
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
    preds = model.predict(X)

    df_out = df.copy()
    df_out["predicted_min"] = preds
    df_out["error_min"] = df_out["predicted_min"] - df_out["duration_min"]
    df_out.to_csv(OUT_CSV, index=False)
    print(f"Wrote predictions to {OUT_CSV}")

    # Plot predicted vs actual
    sns.set(style="whitegrid")
    plt.figure(figsize=(8, 6))
    plt.scatter(df_out["duration_min"], df_out["predicted_min"], alpha=0.7)
    plt.plot([df_out["duration_min"].min(), df_out["duration_min"].max()], [df_out["duration_min"].min(), df_out["duration_min"].max()], color="red", linestyle="--")
    plt.xlabel("Actual duration (min)")
    plt.ylabel("Predicted duration (min)")
    plt.title("Usage Time Model: Predicted vs Actual")
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG)
    print(f"Saved plot to {OUT_PNG}")

    # Print summary metrics
    from sklearn.metrics import mean_squared_error, r2_score
    rmse = mean_squared_error(y, preds, squared=False)
    r2 = r2_score(y, preds)
    print(f"RMSE: {rmse:.4f}  R2: {r2:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-file", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--simulate-users", type=str, default="sim_user1,sim_user2,sim_user3")
    args = parser.parse_args()

    if args.simulate:
        simulate_activity(args.metrics_file, users=[u.strip() for u in args.simulate_users.split(",")])
    evaluate(args.metrics_file, args.model)
