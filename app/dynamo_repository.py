import os
import uuid
import time
from typing import Optional
import boto3
from botocore.exceptions import ClientError
import json

from app.models import EmailSend, SendStatus

# Nombre de la tabla DynamoDB y cola SQS
TABLE_NAME = os.environ.get("EMAIL_SENDS_TABLE", "EmailSends")
QUEUE_URL = os.environ.get("EMAIL_SEND_QUEUE_URL", "") # URL de la cola SQS

dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")
table = dynamodb.Table(TABLE_NAME)

def _now_iso() -> str:
    # timestamp ISO simple tipo 2025-11-01T21:00:00Z
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def save_and_queue(email_send: EmailSend) -> dict:
    """
    Inserta un registro con status=QUEUED en DynamoDB y encola en SQS.
    """
    send_id = str(uuid.uuid4())
    now = _now_iso()

    item = {
        "batch_id": email_send.batch_id,
        "send_id": send_id,
        "email": email_send.email,
        "subject": email_send.subject,
        "content": email_send.content,
        "status": SendStatus.QUEUED.value,
        "created_at": now,
        "updated_at": now,
        "error_message": "",
    }

    message_to_queue = {
        "batch_id": item["batch_id"],
        "send_id": item["send_id"],
        "email": item["email"],
        "subject": item["subject"],
        "content": item["content"],
    }

    try:
        # 1. Guardar en DynamoDB
        table.put_item(Item=item)

        # 2. Enviar a SQS
        if not QUEUE_URL:
            raise RuntimeError("La URL de la cola SQS no está configurada (EMAIL_SEND_QUEUE_URL).")
            
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message_to_queue)
        )
    except ClientError as e:
        # Aquí podrías hacer logging o lanzar excepción HTTP
        raise RuntimeError(f"Error interactuando con AWS: {e}")

    return item
