
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.models import SendStatus

class UploadResult(BaseModel):
    row_number: int
    status: SendStatus
    email: Optional[EmailStr] = None
    error_message: Optional[str] = None


class UploadResponse(BaseModel):
    batch_id: str
    total_rows: int
    successful_imports: int
    failed_imports: int
    results: List[UploadResult]
