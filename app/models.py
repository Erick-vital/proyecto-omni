from enum import Enum
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid


class SendStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    ERROR = "ERROR"


class EmailSend(BaseModel):
    send_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    batch_id: str
    email: EmailStr
    subject: str
    content: str
    status: SendStatus = SendStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
