# digital_twin/twin.py
from __future__ import annotations
from anomaly_detection import detect_anomalies, DEFAULT_RULES

from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, Any, List, Optional


def _to_dt(ts: str | datetime) -> datetime:
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
        info = event.get("info", {})
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

        match tipo:
            case "login":
                u["n_logins"] += 1
                u["login_times"].append(ts)

            case "balance":
                u["n_saldo"] += 1
                # saldo pode vir em info["balance"] (se desejar refletir)
                if "balance" in info:
                    u["saldo"] = float(info["balance"])

            case "deposit":
                valor = float(info.get("amount", 0.0))
                u["n_depositos"] += 1
                u["total_depositado"] += valor
                u["saldo"] += valor
                u["pix_valores"].append(valor)

            case "pix" | "pix_sent":
                valor = float(info.get("amount", 0.0))
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

            case _:
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
            "ultimos_eventos": u["eventos"][-20:],  # último N
        }

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

        avg = {k: (sums[k] / counts[k]) for k in sums}
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

    def anomalies(self, username: str | None = None) -> list[dict[str, Any]]:
        if username:
            evs = self.users.get(username, {}).get("eventos", [])
        else:
            evs = self.eventos
        return detect_anomalies(evs, DEFAULT_RULES)
