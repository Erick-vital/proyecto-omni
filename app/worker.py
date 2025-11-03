
import os
import boto3
import json
from datetime import datetime

def handler(event, context):
    """
    Lambda worker que consume mensajes de SQS, "envía" emails y actualiza DynamoDB.
    """
    print(f"Received {len(event['Records'])} records from SQS.")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["EMAIL_SENDS_TABLE"])

    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            print(f"Processing message: {message}")

            if message.get("content") == "TRIGGER_DLQ":
                raise ValueError("Forced failure for DLQ test")

            # 1. "Enviar" el email (simulación)
            # En un caso real, aquí iría la lógica de envío con SES
            print(f"Simulating email send to {message['email']} with subject '{message['subject']}'")

            # 2. Actualizar estado en DynamoDB a SENT
            table.update_item(
                Key={
                    'batch_id': message['batch_id'],
                    'send_id': message['send_id']
                },
                UpdateExpression="set #status = :s, sent_at = :t",
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':s': 'SENT',
                    ':t': datetime.utcnow().isoformat()
                }
            )
            print(f"Successfully processed and marked as SENT: {message['send_id']}")

        except Exception as e:
            print(f"ERROR processing message: {record['body']}. Error: {e}")
            # Aquí podrías actualizar DynamoDB a ERROR, pero al fallar,
            # SQS lo reintentará y eventualmente lo mandará a la DLQ.
            # Dejamos que el reintento de SQS maneje fallos temporales.

            # Para fallos permanentes, sería bueno tener un estado ERROR.
            # Por simplicidad, lo dejamos así por ahora.

            # Importante: Si la función termina con error, SQS considera que el 
            # mensaje no fue procesado y lo reintentará. Si queremos evitar 
            # reintentos para ciertos errores, debemos asegurarnos de que la 
            # función termine exitosamente (ej. borrando el mensaje de la cola manualmente).
            # En este caso, queremos que reintente, así que propagamos el error.
            raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete.')
    }

