from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TipoEvento(str, Enum):
    deposit = "deposit"
    pix = "pix"
    pix_sent = "pix_sent"
    pix_received = "pix_received"
    login = "login"
    balance = "balance"
    code_analysis = "code_analysis"

class EventInfo(BaseModel):
    user: Optional[str]
    amount: Optional[float]
    to_user: Optional[str]
    balance: Optional[float]

    @validator('amount', 'balance', pre=True)
    def coerce_amount(cls, v):
        if v is None or v == "":
            return None
        try:
            return float(v)
        except Exception:
            raise ValueError('amount/balance must be numeric')

class Event(BaseModel):
    timestamp: Optional[datetime] = None
    tipo: TipoEvento
    info: Optional[EventInfo] = Field(default_factory=dict)
    descricao: Optional[str] = None

    @validator('timestamp', pre=True, always=True)
    def parse_ts(cls, v):
        if v is None:
            return datetime.utcnow()
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(v)
        except Exception:
            raise ValueError('timestamp must be ISO datetime')

    def to_dict(self) -> Dict[str, Any]:
        d = self.dict()
        # serialize timestamp to isoformat for downstream code
        d['timestamp'] = d['timestamp'].isoformat() if d.get('timestamp') else None
        # ensure info uses plain dict
        if isinstance(d.get('info'), EventInfo):
            d['info'] = d['info'].dict()
        return d
