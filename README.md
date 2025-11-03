## Email serverless (objetivo)
Construcción de un sistema serverless en AWS para gestionar campañas de email marketing, permitiendo la ingesta de archivos CSV, procesamiento de envíos, y consulta de estados vía GraphQL.OmniPro Email Serverless

---

## Caracteristicas Principales
*   **Ingesta de CSV:** Endpoint para recibir archivos CSV con datos de email, asunto y contenido.
*   **Procesamiento Asíncrono:** Parseo de CSV y encolamiento de tareas de envío de emails.
*   **Envío de Emails:** Worker para consumir mensajes de la cola y enviar emails (simulado o vía SES).
*   **Persistencia de Estado:** Almacenamiento del estado de cada envío (PENDING | QUEUED | SENT | ERROR).
*   **API GraphQL:** Consulta de estados de envío con filtros por estado y rango de fechas.
*   **Infraestructura como Código (IaC) con Terraform:** Gestión y despliegue de todos los recursos de AWS mediante Terraform.

---
## Arquitectura
El sistema se basa en una arquitectura serverless en AWS, utilizando los siguientes componentes:

*   **API Gateway (HTTP API v2):** Expone los endpoints HTTP para la carga de CSV y la API GraphQL.
*   **AWS Lambda (email-ingestor-lambda):** Función Lambda que actúa como backend para la API Gateway, implementando la lógica de FastAPI para la ingesta de CSV y el endpoint GraphQL.
*   **AWS Lambda (email-sender-worker):** Función Lambda que consume mensajes de una cola SQS, simula el envío de emails y actualiza el estado en DynamoDB.
*   **Amazon SQS (email_send_queue):** Cola estándar utilizada para encolar los mensajes de envío de emails de forma asíncrona.
*   **Amazon SQS (email_send_dlq):** Cola de mensajes fallidos (Dead-Letter Queue) asociada a `email_send_queue` para manejar mensajes que no pudieron ser procesados.
*   **Amazon DynamoDB (EmailSends):** Base de datos NoSQL para persistir el estado de cada envío de email. Incluye un Índice Secundario Global (GSI) `status_index` para consultas eficientes por estado y fecha de creación.
*   **AWS IAM:** Roles y políticas con los permisos mínimos necesarios para que las funciones Lambda interactúen con los demás servicios.

![Diagrama Arquitectura](https://public-temporal.s3.us-east-1.amazonaws.com/Captura+desde+2025-11-03+03-11-15.png)

---

## Despliegue y Configuración
Si realizaste cambios en el app del proyecto tienes que voler a construir al zip,    
ejecuta los siguientes comandos:    
`cp -r app build/package/`    
`cd build/package
zip -r ../lambda_bundle.zip .`    

despues puedes correr los comandos de terraform para desplegar:    
`   
terraform init     
`    
`terraform plan`    
`terraform apply`

## Endpoints
endpoint para subir un archivo csv    
curl:    
```
curl -X POST "https://b5ezqesw53.execute-api.us-east-1.amazonaws.com/campaigns/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@./example.csv"
```

puedes usar el curl para probar el endpoint "/upload"
aunque yo recomiendo usar la documentacion de swagger para probar el endpoint de forma interactiva:    
aqui https://b5ezqesw53.execute-api.us-east-1.amazonaws.com/docs

puedes usar los archivos de prueba de la carpeta /example_csv para probar diferentes casos de prueba

## Graphql
al igual que con el endpoint rest recomiendo probar graphql de forma interactiva desde esta url: https://b5ezqesw53.execute-api.us-east-1.amazonaws.com/graphql

query de ejemplo:    
```
query MyQuery {
    emailSends(status: "SENT") {
    sendId
    batchId
    email
    subject
    status
    createdAt
	}
}
```

## Consideraciones de Diseño y No Funcionales
### Idempotencia
La idempotencia se maneja a nivel de la aplicación al procesar el CSV. Se utiliza un `set` para detectar y saltar emails duplicados dentro del mismo archivo CSV durante la fase de ingesta, evitando que un mismo email sea encolado y procesado múltiples veces si aparece repetido en el archivo.

### Logs y Métricas
*   **Logs:** Las funciones Lambda están configuradas para enviar logs automáticamente a Amazon CloudWatch Logs. Esto permite monitorear la ejecución de las funciones, errores y mensajes de depuración.
*   **Métricas:** CloudWatch Metrics proporciona métricas básicas para las funciones Lambda (invocaciones, errores, duración) y las colas SQS (número de mensajes, mensajes en DLQ).

### Errores y Reintentos
*   **SQS Dead-Letter Queue (DLQ):** La cola `email_send_queue` tiene configurada una DLQ (`email_send_dlq`). Si un mensaje no puede ser procesado exitosamente por la `email-sender-worker` Lambda después de 3 intentos (`maxReceiveCount`), el mensaje se mueve a la DLQ para su posterior análisis y manejo manual o automatizado.

### Seguridad
*   **IAM Roles Mínimos:** Se han definido roles IAM específicos para cada función Lambda (`lambda_ingestor_role` y `lambda_worker_role`) con políticas de permisos mínimos (`lambda_ingestor_policy` y `lambda_worker_policy`). Esto asegura que cada función solo tenga acceso a los recursos de AWS que necesita para operar.
*   **Variables de Entorno:** Los nombres de tablas y URLs de colas se inyectan como variables de entorno en las funciones Lambda, evitando codificar información sensible directamente en el código.

## Evidencias de sistema funcionando
subida exitosa de archivo csv:    
![swagger](https://public-temporal.s3.us-east-1.amazonaws.com/Captura+desde+2025-11-03+03-22-28.png)
query graphql:   
![swagger](https://public-temporal.s3.us-east-1.amazonaws.com/Captura+desde+2025-11-03+03-23-07.png)
historial ded operaciones en dynamodb:    
![dynamodb](https://public-temporal.s3.us-east-1.amazonaws.com/Captura+desde+2025-11-03+03-23-48.png)




## Puntos Adicionales
*   **CI/CD:** Aunque no implementado en este repositorio, se podría integrar fácilmente con GitHub Actions o AWS CodePipeline para automatizar el empaquetado, despliegue y pruebas.
*   **"Dry-run mode":** El worker actual simula el envío de emails. Para un entorno de producción, se integraría con AWS SES. La simulación actual puede considerarse un "dry-run" básico.
*   **`batchId` para agrupar envíos:** El sistema utiliza `batch_id` para agrupar lógicamente los envíos de emails provenientes del mismo archivo CSV, facilitando la consulta y el seguimiento.