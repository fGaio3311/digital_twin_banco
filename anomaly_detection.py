from datetime import datetime, timedelta
from typing import Any, Dict, List

DEFAULT_RULES = {
    "big_deposit": {"tipo": "deposit", "threshold": 10000.0},
    "high_frequency": {"window_minutes": 1, "count": 5},
    "big_pix": {"tipo": "pix", "threshold": 5000.0},
    "strange_moment_activity": {"between_0_and_5AM"}
}

def detect_anomalies(
    events: List[Dict[str, Any]],
    rules: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    anoms = []
    ts_list = [datetime.fromisoformat(ev["timestamp"]) for ev in events]
    cnt_logins = 0
    for ev in events:
        t = ev.get("tipo")
        info = ev.get("info", {})
        ts = datetime.fromisoformat(ev["timestamp"])
        # big_deposit
        if t == rules["big_deposit"]["tipo"] and float(info.get("amount",0)) > rules["big_deposit"]["threshold"]:
            anoms.append({"rule":"big_deposit","evento":ev})
        # big_pix
        if t == rules["big_pix"]["tipo"] and float(info.get("amount",0)) > rules["big_pix"]["threshold"]:
            anoms.append({"rule":"big_pix","evento":ev})
        # high_frequency
        wf = rules["high_frequency"]
        window = timedelta(minutes=wf["window_minutes"])
        cnt = sum(1 for x in ts_list if ts - window <= x <= ts)
        if cnt > wf["count"]:
            anoms.append({"rule":"high_frequency","evento":ev})
        hour = ts.hour
        if 0 <= hour <= 5:
            anoms.append({"rule":"strange_moment_activity", "evento":ev})
        if ev.get("tipo") == "login":
            cnt_logins+=1
            hF = False
            for anom in anoms :
                if anom == {"rule":"high_frequency", "evento":ev}:
                    hF = True
            if cnt_logins > 5 and hF:
                anoms.append({"rule":"brute_force", "evento":ev})
    return anoms
