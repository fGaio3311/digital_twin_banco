from datetime import datetime, timedelta
from typing import Any, Dict, List

DEFAULT_RULES = {
    "big_deposit": {"tipo": "deposit", "threshold": 10000.0, "severity": "MEDIUM"},
    "high_frequency": {"window_minutes": 1, "count": 5, "severity": "HIGH"},
    "big_pix": {"tipo": "pix", "threshold": 5000.0, "severity": "CRITICAL"},
    "strange_moment": {"start_hour": 0, "end_hour": 5, "severity": "HIGH"},
    "brute_force": {"consecutive_logins": 5, "severity": "CRITICAL"}
}

def detect_anomalies(
    events: List[Dict[str, Any]],
    rules: Dict[str, Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    if rules is None:
        rules = DEFAULT_RULES
    anomalies = []
    
    # Agrupando por usuário para evitar cross-contamination nas regras stateful
    users_events = {}
    for ev in events:
        usr = ev.get("info", {}).get("user", "unknown")
        if usr not in users_events:
            users_events[usr] = []
        users_events[usr].append(ev)

    for usr, u_events in users_events.items():
        # Ordenando cronologicamente os eventos do usuário
        u_events.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]))
        login_streak = 0
        
        for i, ev in enumerate(u_events):
            t = ev.get("tipo")
            info = ev.get("info", {})
            ts = datetime.fromisoformat(ev["timestamp"])
            amt = float(info.get("amount", 0.0))
            
            # 1. Regra BACEN: Pix ou deposito massivo
            if t == rules["big_deposit"]["tipo"] and amt >= rules["big_deposit"]["threshold"]:
                anomalies.append({"rule": "big_deposit", "severity": rules["big_deposit"]["severity"], "evento": ev})
            
            if t == rules["big_pix"]["tipo"] and amt >= rules["big_pix"]["threshold"]:
                anomalies.append({"rule": "big_pix", "severity": rules["big_pix"]["severity"], "evento": ev})
            
            # 2. Transações Madrugada (BACEN Pix Noturno)
            hour = ts.hour
            if rules["strange_moment"]["start_hour"] <= hour <= rules["strange_moment"]["end_hour"]:
                anomalies.append({"rule": "strange_moment", "severity": rules["strange_moment"]["severity"], "evento": ev})
                
            # 3. High Frequency (Vários PIX ou requests em 1 minuto)
            wf = rules["high_frequency"]
            window = timedelta(minutes=wf["window_minutes"])
            count_in_window = 0
            for j in range(i, -1, -1):
                ts_prev = datetime.fromisoformat(u_events[j]["timestamp"])
                if ts - ts_prev <= window:
                    count_in_window += 1
                else:
                    break
            
            if count_in_window >= wf["count"]:
                anomalies.append({"rule": "high_frequency", "severity": wf["severity"], "evento": ev})
                
            # 4. Brute Force Logins
            if t == "login":
                login_streak += 1
                if login_streak >= rules["brute_force"]["consecutive_logins"]:
                    anomalies.append({"rule": "brute_force", "severity": rules["brute_force"]["severity"], "evento": ev})
            else:
                login_streak = 0

    return anomalies

def evaluate_fraud_score(anomalies: List[Dict[str, Any]]) -> float:
    """Calcula um risco de fraude 0-100 para interceptação em tempo real pelo Gêmeo."""
    score = 0.0
    for a in anomalies:
        sev = a.get("severity", "LOW")
        if sev == "CRITICAL":
            score += 40.0
        elif sev == "HIGH":
            score += 25.0
        elif sev == "MEDIUM":
            score += 15.0
        else:
            score += 5.0
    return min(100.0, score)
