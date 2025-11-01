from .models import EmailSend, SendStatus
from datetime import datetime
from typing import List, Optional, Tuple
import uuid


# In-memory database
db: List[EmailSend] = []


class EmailRepository:
    def save_pending(self, email_send: EmailSend) -> None:
        ...

    def mark_sent(self, send_id: str, batch_id: str) -> None:
        ...

    def mark_error(self, send_id: str, batch_id: str, error_message: str) -> None:
        ...

    def query_status(
        self,
        statuses: list[SendStatus],
        date_from: datetime | None,
        date_to: datetime | None,
        limit: int = 50,
        next_token: str | None = None,
    ) -> tuple[list[EmailSend], str | None]:
        ...


class InMemoryEmailRepository(EmailRepository):
    def __init__(self, database: List[EmailSend]):
        self._db = database

    def save_pending(self, email_send: EmailSend) -> None:
        self._db.append(email_send)


# Global repository instance
email_repository = InMemoryEmailRepository(database=db)
