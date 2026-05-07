from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, validator


class TipoEvento(str, Enum):
    deposit = "deposit"
    pix = "pix"
    pix_sent = "pix_sent"
    pix_received = "pix_received"
    login = "login"
    balance = "balance"
    code_analysis = "code_analysis"
    http_request = "http_request"
    security_alert = "security_alert"


class EventInfo(BaseModel):
    user: Optional[str] = None
    amount: Optional[float] = None
    to_user: Optional[str] = None
    balance: Optional[float] = None
    ip: Optional[str] = None
    geo: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status: Optional[int] = None
    latency_ms: Optional[float] = None
    payload: Optional[str] = None

    @validator("amount", "balance", pre=True)
    def coerce_amount(cls, v: object) -> Optional[float]:
        if v is None or v == "":
            return None
        if isinstance(v, (str, int, float)):
            try:
                return float(v)
            except ValueError:
                raise ValueError("amount/balance must be numeric")
        raise ValueError("amount/balance must be numeric")


class Event(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tipo: Union[TipoEvento, str]
    info: Union[EventInfo, Dict[str, Any]] = Field(default_factory=EventInfo)
    descricao: Optional[str] = None

    @validator("timestamp", pre=True)
    def parse_ts(cls, v: object) -> datetime:
        if v is None:
            return datetime.utcnow()
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                raise ValueError("timestamp must be ISO datetime")
        raise ValueError("timestamp must be ISO datetime")

    def to_dict(self) -> Dict[str, Any]:
        d = self.dict()
        d["timestamp"] = d["timestamp"].isoformat() if d.get("timestamp") else None
        if isinstance(d.get("tipo"), Enum):
            d["tipo"] = d["tipo"].value
        return d
