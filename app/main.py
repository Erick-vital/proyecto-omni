from fastapi import FastAPI, File, UploadFile, HTTPException, status
from .repository import email_repository
from .models import EmailSend, SendStatus, UploadResult, UploadResponse
import csv
import io
import uuid
from typing import List

app = FastAPI()

MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@app.post("/upload", response_model=UploadResponse, status_code=status.HTTP_200_OK)
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV"
        )

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the limit of {MAX_FILE_SIZE_MB}MB",
        )

    batch_id = str(uuid.uuid4())
    stream = io.StringIO(file_content.decode("utf-8"))
    csv_reader = csv.DictReader(stream)

    required_columns = {"email", "subject", "content"}
    if not csv_reader.fieldnames or not required_columns.issubset(
        csv_reader.fieldnames
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV must have the following columns: {', '.join(required_columns)}",
        )

    emails_to_save: List[EmailSend] = []
    upload_results: List[UploadResult] = []
    successful_imports = 0
    failed_imports = 0
    total_rows = 0

    for i, row in enumerate(csv_reader):
        total_rows += 1
        row_number = i + 2  # +1 for 0-based index, +1 for header row

        try:
            email_data = EmailSend(
                batch_id=batch_id,
                email=row["email"],
                subject=row["subject"],
                content=row["content"],
            )
            emails_to_save.append(email_data)
            upload_results.append(
                UploadResult(
                    row_number=row_number,
                    status=SendStatus.PENDING,
                    email=email_data.email,
                )
            )
            successful_imports += 1
        except Exception as e:
            failed_imports += 1
            upload_results.append(
                UploadResult(
                    row_number=row_number,
                    status=SendStatus.ERROR,
                    email=row.get("email"),
                    error_message=str(e),
                )
            )

    if emails_to_save:
        email_repository.save_many_pending(emails_to_save)

    return UploadResponse(
        batch_id=batch_id,
        total_rows=total_rows,
        successful_imports=successful_imports,
        failed_imports=failed_imports,
        results=upload_results,
    )


@app.get("/")
async def root():
    return {"message": "Hello World"}
