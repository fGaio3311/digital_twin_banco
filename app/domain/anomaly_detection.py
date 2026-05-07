from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

DEFAULT_RULES: Dict[str, Dict[str, Any]] = {
    "big_deposit": {"tipo": "deposit", "threshold": 10000.0, "severity": "MEDIUM"},
    "high_frequency": {"window_minutes": 1, "count": 5, "severity": "HIGH"},
    "big_pix": {
        "tipos": ["pix", "pix_sent"],
        "threshold": 5000.0,
        "severity": "CRITICAL",
    },
    "strange_moment": {"start_hour": 0, "end_hour": 5, "severity": "HIGH"},
    "brute_force": {"consecutive_logins": 5, "severity": "CRITICAL"},
    "risky_geo": {
        "geos": ["CN", "RU", "CHINA", "RUSSIA", "RÚSSIA"],
        "severity": "CRITICAL",
    },
    "server_error": {"status": 500, "severity": "HIGH"},
    "data_exfiltration": {
        "endpoints": ["/admin/export", "/export", "/logs/export"],
        "severity": "CRITICAL",
    },
}

PAYLOAD_SIGNATURES: Dict[str, List[str]] = {
    "xss": ["<script", "onerror=", "onload=", "javascript:", "<img"],
    "sqli": ["union select", "' or 1=1", '" or 1=1', "drop table", "--", "/*", "xp_"],
    "path_traversal": ["../", "..\\"],
}


def _event_info(event: Dict[str, Any]) -> Dict[str, Any]:
    info = event.get("info")
    return info if isinstance(info, dict) else {}


def _parse_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()


def _as_float(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, (str, int, float)):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _as_int(value: object, default: int = 0) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, (str, int, float)):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _append_anomaly(
    anomalies: List[Dict[str, Any]], rule: str, severity: str, event: Dict[str, Any]
) -> None:
    anomalies.append({"rule": rule, "severity": severity, "evento": event})


def detect_anomalies(
    events: List[Dict[str, Any]], rules: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    active_rules = rules or DEFAULT_RULES
    anomalies: List[Dict[str, Any]] = []
    users_events: Dict[str, List[Dict[str, Any]]] = {}

    for event in events:
        info = _event_info(event)
        user = str(info.get("user") or "unknown")
        users_events.setdefault(user, []).append(event)

    for user_events in users_events.values():
        user_events.sort(key=lambda item: _parse_timestamp(item.get("timestamp")))
        login_streak = 0

        for index, event in enumerate(user_events):
            event_type = str(event.get("tipo") or "")
            info = _event_info(event)
            ts = _parse_timestamp(event.get("timestamp"))
            amount = _as_float(info.get("amount"))

            big_deposit = active_rules["big_deposit"]
            if event_type == big_deposit["tipo"] and amount >= float(
                big_deposit["threshold"]
            ):
                _append_anomaly(
                    anomalies, "big_deposit", str(big_deposit["severity"]), event
                )

            big_pix = active_rules["big_pix"]
            if event_type in big_pix["tipos"] and amount >= float(big_pix["threshold"]):
                _append_anomaly(anomalies, "big_pix", str(big_pix["severity"]), event)

            risky_geo = active_rules["risky_geo"]
            geo = str(info.get("geo") or "").upper()
            if geo in risky_geo["geos"]:
                _append_anomaly(
                    anomalies, "risky_geo", str(risky_geo["severity"]), event
                )

            server_error = active_rules["server_error"]
            status = _as_int(info.get("status"))
            if status >= int(server_error["status"]):
                _append_anomaly(
                    anomalies, "server_error", str(server_error["severity"]), event
                )

            data_exfiltration = active_rules["data_exfiltration"]
            endpoint = str(info.get("endpoint") or "").lower()
            if endpoint in data_exfiltration["endpoints"]:
                _append_anomaly(
                    anomalies,
                    "data_exfiltration",
                    str(data_exfiltration["severity"]),
                    event,
                )

            strange_moment = active_rules["strange_moment"]
            if (
                int(strange_moment["start_hour"])
                <= ts.hour
                <= int(strange_moment["end_hour"])
            ):
                _append_anomaly(
                    anomalies, "strange_moment", str(strange_moment["severity"]), event
                )

            high_frequency = active_rules["high_frequency"]
            window = timedelta(minutes=int(high_frequency["window_minutes"]))
            count_in_window = 0
            for previous_index in range(index, -1, -1):
                previous_ts = _parse_timestamp(
                    user_events[previous_index].get("timestamp")
                )
                if ts - previous_ts <= window:
                    count_in_window += 1
                else:
                    break

            if count_in_window >= int(high_frequency["count"]):
                _append_anomaly(
                    anomalies, "high_frequency", str(high_frequency["severity"]), event
                )

            if event_type == "login":
                login_streak += 1
                brute_force = active_rules["brute_force"]
                if login_streak >= int(brute_force["consecutive_logins"]):
                    _append_anomaly(
                        anomalies, "brute_force", str(brute_force["severity"]), event
                    )
            else:
                login_streak = 0

    return anomalies


def evaluate_fraud_score(anomalies: List[Dict[str, Any]]) -> float:
    """Calcula um risco de fraude 0-100 para interceptação em tempo real pelo Gêmeo."""
    score = 0.0
    for anomaly in anomalies:
        severity = anomaly.get("severity", "LOW")
        if severity == "CRITICAL":
            score += 40.0
        elif severity == "HIGH":
            score += 25.0
        elif severity == "MEDIUM":
            score += 15.0
        else:
            score += 5.0
    return min(100.0, score)


def detect_payload_signatures(payload: str) -> List[str]:
    if not payload:
        return []
    payload_low = payload.lower()
    return [
        name
        for name, signatures in PAYLOAD_SIGNATURES.items()
        if any(signature in payload_low for signature in signatures)
    ]


def score_event(event: Dict[str, Any], user_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Score 0-100 based on velocity, UEBA, and payload signatures."""
    info = _event_info(event)
    amount = _as_float(info.get("amount"))
    payload = str(info.get("payload") or "")
    geo = str(info.get("geo") or "").upper()
    status = _as_int(info.get("status"))
    endpoint = str(info.get("endpoint") or "").lower()

    now = _parse_timestamp(event.get("timestamp"))
    window = timedelta(minutes=1)
    recent = [
        item
        for item in user_events
        if _parse_timestamp(item.get("timestamp")) >= now - window
    ]
    velocity_score = min(40.0, len(recent) * 5.0)

    amounts = [_as_float(_event_info(item).get("amount")) for item in user_events]
    median = 0.0
    if amounts:
        sorted_amounts = sorted(amounts)
        median = sorted_amounts[len(sorted_amounts) // 2]

    ueba_score = 0.0
    if median > 0:
        ratio = amount / median
        if ratio >= 10:
            ueba_score = 30.0
        elif ratio >= 5:
            ueba_score = 20.0
        elif ratio >= 2:
            ueba_score = 10.0

    big_pix_threshold = float(DEFAULT_RULES["big_pix"]["threshold"])
    amount_score = 0.0
    if amount >= 500000:
        amount_score = 60.0
    elif amount >= 50000:
        amount_score = 40.0
    elif amount >= big_pix_threshold:
        amount_score = 25.0

    payload_hits = detect_payload_signatures(payload)
    payload_score = 40.0 if payload_hits else 0.0

    geo_score = 25.0 if geo in DEFAULT_RULES["risky_geo"]["geos"] else 0.0
    server_error_status = int(DEFAULT_RULES["server_error"]["status"])
    error_score = 30.0 if status >= server_error_status else 0.0
    exfil_score = (
        30.0 if endpoint in DEFAULT_RULES["data_exfiltration"]["endpoints"] else 0.0
    )

    anomalies = detect_anomalies(user_events + [event])
    anomaly_score = evaluate_fraud_score(anomalies)

    total = min(
        100.0,
        velocity_score
        + ueba_score
        + amount_score
        + payload_score
        + geo_score
        + error_score
        + exfil_score
        + anomaly_score * 0.4,
    )
    return {
        "score": total,
        "velocity_score": velocity_score,
        "ueba_score": ueba_score,
        "amount_score": amount_score,
        "payload_score": payload_score,
        "payload_hits": payload_hits,
        "geo_score": geo_score,
        "error_score": error_score,
        "exfil_score": exfil_score,
        "anomalies": anomalies,
    }
