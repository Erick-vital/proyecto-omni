
import strawberry
import datetime
from typing import Optional

@strawberry.type
class EmailSend:
    send_id: str
    batch_id: str
    email: str
    subject: str
    content: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    sent_at: Optional[datetime.datetime] = None
    error_message: Optional[str] = None
