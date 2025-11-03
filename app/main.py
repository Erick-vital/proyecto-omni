import uuid
import csv
import io
from typing import Set

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from mangum import Mangum

# Asumimos que estos módulos existen según el contexto proporcionado
from app.models import EmailSend, SendStatus
from app import dynamo_repository

# --- Constantes ---
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
REQUIRED_COLUMNS = ["email", "subject", "content"]

# --- Aplicación FastAPI ---
app = FastAPI(
    title="OmniPro Email Ingestion Service",
    description="API para la ingestión de campañas de email por lotes.",
    version="0.1.0",
)

# --- Endpoints ---

@app.get("/", summary="Endpoint de Bienvenida", tags=["General"])
def read_root() -> dict:
    """
    Endpoint de prueba que devuelve un mensaje de bienvenida.
    """
    return {"message": "Hello World"}


@app.post("/upload", summary="Cargar CSV de Campaña", tags=["Campaigns"])
async def upload_campaign_csv(file: UploadFile = File(...)) -> dict:
    """
    Procesa un archivo CSV para una campaña de email.

    - Valida que el archivo sea .csv y no exceda el límite de tamaño.
    - Valida la presencia de las columnas requeridas: `email`, `subject`, `content`.
    - Evita emails duplicados dentro del mismo archivo.
    - Registra los envíos válidos con estado PENDING.
    - Devuelve un resumen del lote procesado.
    """
    # 1. Validación del tipo de archivo
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe tener extensión .csv",
        )

    # 2. Validación del tamaño del archivo
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el límite de {MAX_FILE_SIZE / 1024 / 1024} MB.",
        )

    # 3. Procesamiento del CSV
    batch_id = str(uuid.uuid4())
    total_count = 0
    enqueued_count = 0
    skipped_count = 0
    seen_emails: Set[str] = set()

    try:
        file_text = contents.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(file_text))

        for row in csv_reader:
            total_count += 1
            email = row.get("email", "").strip()

            # Validar columnas requeridas y que el email no esté duplicado
            if (
                not all(key in row for key in REQUIRED_COLUMNS)
                or not email
                or email in seen_emails
            ):
                skipped_count += 1
                continue

            seen_emails.add(email)

            # Crear el objeto de envío
            email_send = EmailSend(
                batch_id=batch_id,
                email=email,
                subject=row.get("subject"),
                content=row.get("content"),
                status=SendStatus.PENDING,
            )

            dynamo_repository.save_and_queue(email_send)
            enqueued_count += 1

    except Exception as e:
        # Captura errores de decodificación o malformación del CSV
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error al procesar el archivo CSV: {e}",
        )

    return {
        "batchId": batch_id,
        "total": total_count,
        "enqueued": enqueued_count,
        "skipped": skipped_count,
    }


# --- AWS Lambda Handler ---
# Esta es la entrada para AWS Lambda a través de API Gateway.
handler = Mangum(app)


# --- Ejecución Local ---
# Este bloque permite correr la app localmente con Uvicorn para desarrollo.
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )