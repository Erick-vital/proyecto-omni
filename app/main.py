from fastapi import FastAPI, File, UploadFile, HTTPException
from .repository import email_repository
from .models import EmailSend
import csv
import io
import uuid

app = FastAPI()


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    batch_id = str(uuid.uuid4())
    content = await file.read()
    stream = io.StringIO(content.decode("utf-8"))
    csv_reader = csv.DictReader(stream)

    emails_to_create = []
    required_columns = {"email", "subject", "content"}

    if not required_columns.issubset(csv_reader.fieldnames):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have the following columns: {required_columns}",
        )

    for row in csv_reader:
        email_data = EmailSend(
            batch_id=batch_id,
            email=row["email"],
            subject=row["subject"],
            content=row["content"],
        )
        emails_to_create.append(email_data)

    for email_data in emails_to_create:
        email_repository.save_pending(email_data)

    return {
        "message": f"{len(emails_to_create)} emails registered successfully",
        "batch_id": batch_id,
    }


@app.get("/")
async def root():
    return {"message": "Hello World"}
