# digital_twin/twin.py
from __future__ import annotations
from app.domain.anomaly_detection import detect_anomalies, DEFAULT_RULES
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, Any, List, Optional


def _to_dt(ts: Any) -> datetime:
    if isinstance(ts, datetime):
        return ts
    return datetime.fromisoformat(ts)


class DigitalTwin:
    """
    Twin em memória, alimentado por eventos MQTT/Logger.
    Nenhum acesso a arquivo físico. Export = retorna lista (para API/cliente salvar se quiser).
    """

    def __init__(self):
        # estado agregado por usuário
        self.users: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "saldo": 0.0,
            "n_logins": 0,
            "n_saldo": 0,
            "n_depositos": 0,
            "n_pix": 0,
            "total_depositado": 0.0,
            "total_pix_enviado": 0.0,
            "total_pix_recebido": 0.0,
            "eventos": [],           # eventos brutos (shadow)
            "login_times": [],
            "pix_valores": [],
            "last_event_ts": None,   # datetime
            "counters": Counter(),   # contagem genérica por tipo
        })

        # eventos globais p/ stats/sazonalidade
        self.eventos: List[Dict[str, Any]] = []

        # bucket especial para code_analysis, logs de pre-commit, etc.
        self.users["precommit"] = {"eventos": []}
        # usage model (optional)
        self._usage_model = None
        self._usage_model_features = [
            "num_requests",
            "mean_latency_ms",
            "median_latency_ms",
            "std_latency_ms",
            "error_rate",
            "unique_endpoints",
            "start_hour",
            "day_of_week",
        ]

    # ------------------ Entrada ------------------
    def apply_event(self, event: Dict[str, Any]) -> None:
        """
        Formato esperado:
        {
          "timestamp": "...iso...",
          "tipo": "deposit"|"pix"|"login"|...,
          "info": {"user": "...", "amount": 10.0, "to_user": "...", "balance": 42.0},
          "descricao": "..."
        }
        """
        # Normaliza
        ts = event.get("timestamp") or datetime.utcnow().isoformat()
        event["timestamp"] = ts

        tipo = event.get("tipo")
        info = event.get("info") or {}
        if not isinstance(info, dict):
            info = {}
        user = info.get("user")

        # Guarda global
        self.eventos.append(event)

        # Code analysis / outros buckets
        if tipo == "code_analysis":
            self.users["precommit"]["eventos"].append(event)
            return

        # Ignora se não há user/tipo
        if not user or not tipo:
            return

        u = self.users[user]
        u["eventos"].append(event)
        u["counters"][tipo] += 1
        u["last_event_ts"] = _to_dt(ts) if (u["last_event_ts"] is None or _to_dt(ts) > u["last_event_ts"]) else u["last_event_ts"]

        if tipo == "login":
            u["n_logins"] += 1
            u["login_times"].append(ts)
        elif tipo == "balance":
            u["n_saldo"] += 1
            # saldo pode vir em info["balance"] (se desejar refletir)
            if "balance" in info:
                try:
                    u["saldo"] = float(info["balance"])
                except (TypeError, ValueError):
                    pass
        elif tipo == "deposit":
            try:
                valor = float(info.get("amount", 0.0))
            except (TypeError, ValueError):
                valor = 0.0
            u["n_depositos"] += 1
            u["total_depositado"] += valor
            u["saldo"] += valor
            u["pix_valores"].append(valor)
        elif tipo in ("pix", "pix_sent"):
            try:
                valor = float(info.get("amount", 0.0))
            except (TypeError, ValueError):
                valor = 0.0
            to_user = info.get("to_user")
            u["n_pix"] += 1
            u["total_pix_enviado"] += valor
            u["saldo"] -= valor
            u["pix_valores"].append(valor)

            # Atualiza destinatário (se existir)
            if to_user:
                r = self.users[to_user]
                r["total_pix_recebido"] += valor
                r["saldo"] += valor
                r["pix_valores"].append(valor)
                r["counters"]["pix_received"] += 1
        else:
            # Outros tipos: só incrementa contadores e guarda evento
            pass

    # ------------------ Consultas ------------------
    def get_shadow(self, username: str) -> Dict[str, Any]:
        u = self.users.get(username)
        if not u:
            return {"erro": "Usuário não encontrado"}
        return {
            "username": username,
            "saldo": u["saldo"],
            "last_event_ts": u["last_event_ts"].isoformat() if u["last_event_ts"] else None,
            "n_logins": u["n_logins"],
            "n_depositos": u["n_depositos"],
            "n_pix": u["n_pix"],
            "total_depositado": u["total_depositado"],
            "total_pix_enviado": u["total_pix_enviado"],
            "total_pix_recebido": u["total_pix_recebido"],
            "counters": dict(u["counters"]),
            "eventos": u["eventos"],  # último N
        }
    def get_janela_de_logins(self):
        # Retorna os eventos do tipo 'login' em janela agregada (global)
        return [ev for ev in self.eventos if ev.get("tipo") == "login"]

    def summary(self) -> Dict[str, Any]:
        return {
            user: {
                "saldo": data["saldo"],
                "n_logins": data["n_logins"],
                "n_saldo": data["n_saldo"],
                "n_depositos": data["n_depositos"],
                "n_pix": data["n_pix"],
                "total_depositado": data["total_depositado"],
                "total_pix_enviado": data["total_pix_enviado"],
                "total_pix_recebido": data["total_pix_recebido"],
            }
            for user, data in self.users.items()
            if user != "precommit"
        }

    def stats(self) -> Dict[str, Any]:
        tipos = Counter()
        sums = defaultdict(float)
        counts = Counter()

        for ev in self.eventos:
            t = ev.get("tipo")
            if t:
                tipos[t] += 1
            amt = ev.get("info", {}).get("amount")
            if isinstance(amt, (int, float)):
                sums[t] += float(amt)
                counts[t] += 1

        # Evitar divisão por zero: somente calcula média quando houver contagem
        avg = {k: (sums[k] / counts[k]) for k in sums if counts[k] > 0}
        return {
            "count_by_type": dict(tipos),
            "sum_by_type": dict(sums),
            "avg_by_type": avg,
            "total_events": len(self.eventos),
            "total_users": len([u for u in self.users if u != 'precommit']),
        }

    def sazonalidade(self) -> Dict[str, Any]:
        by_hour = Counter()
        by_weekday = Counter()   # 0 = Monday
        by_month = Counter()

        for ev in self.eventos:
            ts = ev.get("timestamp")
            try:
                dt = _to_dt(ts)
            except (ValueError, TypeError):
                # Skip events with invalid timestamps
                continue
            by_hour[dt.hour] += 1
            by_weekday[dt.weekday()] += 1
            by_month[f"{dt.year}-{dt.month:02d}"] += 1

        return {
            "by_hour": dict(sorted(by_hour.items())),
            "by_weekday": dict(sorted(by_weekday.items())),  # 0..6
            "by_month": dict(sorted(by_month.items())),
        }

    def export_events(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        if username:
            u = self.users.get(username)
            return u["eventos"] if u else []
        return self.eventos

    def anomalies(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        if username:
            evs = self.users.get(username, {}).get("eventos", [])
        else:
            evs = self.eventos
        return detect_anomalies(evs, DEFAULT_RULES)

    # ------------------ Model integration ------------------
    def load_usage_model(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Model file not found: {p}")
        self._usage_model = joblib.load(p)

    def predict_user_last_session(self, username: str, session_gap_minutes: int = 30) -> Optional[Dict[str, Any]]:
        """Build features for the user's last session and predict duration (minutes).
        Returns a dict with `features`, `predicted_duration_min` and `model_info`.
        """
        if self._usage_model is None:
            raise RuntimeError("Usage model not loaded. Call load_usage_model(path) first.")

        u = self.users.get(username)
        if not u:
            return None

        # Build last session from user's events based on gap
        from datetime import datetime, timedelta

        evs = [e for e in u.get("eventos", []) if e.get("timestamp")]
        if not evs:
            return None
        for e in evs:
            if not isinstance(e.get("_dt"), datetime):
                e["_dt"] = datetime.fromisoformat(e["timestamp"])
        evs.sort(key=lambda x: x["_dt"])
        gap = timedelta(minutes=session_gap_minutes)
        # find last session block
        last_session = []
        last_ts = None
        for e in reversed(evs):
            if last_ts is None:
                last_session.insert(0, e)
                last_ts = e["_dt"]
                continue
            if last_ts - e["_dt"] > gap:
                break
            last_session.insert(0, e)
            last_ts = e["_dt"]

        if not last_session:
            return None

        # compute features similar to tools/usage_time_regression.make_session_record
        latencies = [float(e.get("latency_ms", 0.0)) for e in last_session]
        endpoints = [e.get("endpoint") for e in last_session]
        successes = [bool(e.get("success", True)) for e in last_session]
        start = last_session[0]["_dt"]
        duration_min = max(0.0, (last_session[-1]["_dt"] - start).total_seconds() / 60.0)

        feat = {
            "num_requests": len(last_session),
            "mean_latency_ms": float(np.mean(latencies)) if latencies else 0.0,
            "median_latency_ms": float(np.median(latencies)) if latencies else 0.0,
            "std_latency_ms": float(np.std(latencies)) if latencies else 0.0,
            "error_rate": float(1.0 - sum(1 for s in successes if s) / len(successes)) if successes else 0.0,
            "unique_endpoints": len(set(endpoints)),
            "start_hour": start.hour,
            "day_of_week": start.weekday(),
        }

        X = pd.DataFrame([feat])[self._usage_model_features].astype(float)
        pred = float(self._usage_model.predict(X)[0])

        return {"features": feat, "predicted_duration_min": pred, "actual_duration_min": duration_min}
