# digital_twin/anomaly.py
from __future__ import annotations
from datetime import datetime, time
from typing import Dict, Any, List

DEFAULT_RULES = {
    "pix_high_value": 10_000.0,        # PIX acima disso é suspeito
    "deposit_high_value": 50_000.0,
    "night_activity_start": time(0,0), # 00:00
    "night_activity_end":   time(5,0), # 05:00
    "max_pix_per_hour": 5,             # mais que X PIX/hora
}

def detect_anomalies(events: List[Dict[str, Any]], rules: Dict[str, Any] = DEFAULT_RULES) -> List[Dict[str, Any]]:
    """Recebe lista de eventos (globais ou por usuário) e retorna lista de anomalias."""
    anomalies = []
    # índice por hora para contagem de pix
    pix_count_by_hour = {}

    for ev in events:
        tipo = ev.get("tipo")
        info = ev.get("info", {})
        amt = info.get("amount", 0)
        ts = ev.get("timestamp")
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            # Skip events with invalid timestamps
            continue

        # High value rules
        if tipo in ("pix", "pix_sent") and amt >= rules["pix_high_value"]:
            anomalies.append({"rule": "pix_high_value", "event": ev})
        if tipo == "deposit" and amt >= rules["deposit_high_value"]:
            anomalies.append({"rule": "deposit_high_value", "event": ev})

        # Night activity
        if rules["night_activity_start"] <= dt.time() <= rules["night_activity_end"]:
            anomalies.append({"rule": "night_activity", "event": ev})

        # Pix flood per hour
        if tipo in ("pix", "pix_sent"):
            key = (info.get("user"), dt.replace(minute=0, second=0, microsecond=0))
            pix_count_by_hour[key] = pix_count_by_hour.get(key, 0) + 1
            if pix_count_by_hour[key] > rules["max_pix_per_hour"]:
                anomalies.append({"rule": "pix_rate_limit_hour", "event": ev, "count_hour": pix_count_by_hour[key]})

    return anomalies
