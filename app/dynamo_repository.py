import os
import uuid
import time
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from app.models import EmailSend, SendStatus

# Nombre de la tabla DynamoDB
TABLE_NAME = os.environ.get("EMAIL_SENDS_TABLE", "EmailSends")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def _now_iso() -> str:
    # timestamp ISO simple tipo 2025-11-01T21:00:00Z
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def save_pending(email_send: EmailSend) -> dict:
    """
    Inserta un registro con status=PENDING en DynamoDB.
    Genera send_id único y rellena timestamps.
    Devuelve el item guardado (útil para debug / logging).
    """

    send_id = str(uuid.uuid4())

    item = {
        "batch_id": email_send.batch_id,        # PK
        "send_id": send_id,                     # SK
        "email": email_send.email,
        "subject": email_send.subject,
        "content": email_send.content,
        "status": SendStatus.PENDING.value 
                 if hasattr(SendStatus, "PENDING") 
                 else "PENDING",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        # Podemos incluir error_message vacío
        "error_message": "",
    }

    try:
        table.put_item(Item=item)
    except ClientError as e:
        # Aquí podrías hacer logging o lanzar excepción HTTP
        raise RuntimeError(f"Error guardando en DynamoDB: {e}")

    return item

def mark_sent(batch_id: str, send_id: str) -> None:
    """
    Ejemplo de actualización de estado a SENT (futuro worker).
    """
    try:
        table.update_item(
            Key={
                "batch_id": batch_id,
                "send_id": send_id,
            },
            UpdateExpression="SET #st = :st, updated_at = :now",
            ExpressionAttributeNames={
                "#st": "status",
            },
            ExpressionAttributeValues={
                ":st": "SENT",
                ":now": _now_iso(),
            },
        )
    except ClientError as e:
        raise RuntimeError(f"Error actualizando estado en DynamoDB: {e}")

def mark_error(batch_id: str, send_id: str, message: str) -> None:
    """
    Ejemplo de actualizar a ERROR con mensaje.
    """
    try:
        table.update_item(
            Key={
                "batch_id": batch_id,
                "send_id": send_id,
            },
            UpdateExpression="""
                SET #st = :st,
                    error_message = :msg,
                    updated_at = :now
            """,
            ExpressionAttributeNames={
                "#st": "status",
            },
            ExpressionAttributeValues={
                ":st": "ERROR",
                ":msg": message,
                ":now": _now_iso(),
            },
        )
    except ClientError as e:
        raise RuntimeError(f"Error marcando error en DynamoDB: {e}")
