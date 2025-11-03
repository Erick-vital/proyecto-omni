
import strawberry
import datetime
from typing import List, Optional
import boto3
from boto3.dynamodb.conditions import Key
import os
from strawberry.fastapi import GraphQLRouter

from app.schemas.graphql import EmailSend

# Nombre de la tabla y el índice
TABLE_NAME = os.environ.get("EMAIL_SENDS_TABLE", "EmailSends")
STATUS_INDEX_NAME = "status_index"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

@strawberry.type
class Query:
    @strawberry.field
    def email_sends(
        self,
        status: Optional[str] = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> List[EmailSend]:
        """Resuelve la consulta de envíos de email con filtros."""
        
        # Si se provee un status, usamos el GSI
        if status:
            key_condition = Key('status').eq(status)
            
            # Si hay fechas, las añadimos a la condición
            if start_date and end_date:
                key_condition = key_condition & Key('created_at').between(
                    start_date.isoformat(), end_date.isoformat()
                )
            elif start_date:
                key_condition = key_condition & Key('created_at').gte(start_date.isoformat())
            elif end_date:
                key_condition = key_condition & Key('created_at').lte(end_date.isoformat())

            response = table.query(
                IndexName=STATUS_INDEX_NAME,
                KeyConditionExpression=key_condition
            )
        # Si no hay status, hacemos un Scan (menos eficiente)
        else:
            # En un caso real, aquí deberíamos implementar paginación
            # Por simplicidad, limitamos el scan a 100 items
            response = table.scan(Limit=100)

        items = response.get("Items", [])

        # Convertir strings de fecha a objetos datetime
        result = []
        for item in items:
            item['created_at'] = datetime.datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            item['updated_at'] = datetime.datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            if item.get('sent_at'):
                item['sent_at'] = datetime.datetime.fromisoformat(item['sent_at'].replace('Z', '+00:00'))
            result.append(EmailSend(**item))

        return result

schema = strawberry.Schema(query=Query)

graphql_router = GraphQLRouter(schema)
