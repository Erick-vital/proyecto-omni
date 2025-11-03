
# IAM Role y Policy para el Worker Lambda
resource "aws_iam_role" "lambda_worker_role" {
  name = "lambda-worker-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_policy" "lambda_worker_policy" {
  name        = "lambda-worker-policy"
  description = "Permisos para Lambda worker (SQS, DynamoDB, Logs)"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SQSRead",
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "${aws_sqs_queue.email_send_queue.arn}"
    },
    {
      "Sid": "DynamoWrite",
      "Effect": "Allow",
      "Action": [
        "dynamodb:UpdateItem"
      ],
      "Resource": "${aws_dynamodb_table.email_sends.arn}"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:${var.aws_region}:*:*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_worker_role_attach" {
  role       = aws_iam_role.lambda_worker_role.name
  policy_arn = aws_iam_policy.lambda_worker_policy.arn
}

# Lambda Function para el Worker
resource "aws_lambda_function" "email_sender_worker" {
  function_name = "email-sender-worker"

  # Asumimos que el mismo paquete ZIP contiene el código del worker
  # En un proyecto real, esto podría ser un ZIP separado
  filename         = var.lambda_package_zip
  source_code_hash = filebase64sha256(var.lambda_package_zip)

  handler = "app.worker.handler" # El handler del worker
  runtime = "python3.12"
  role    = aws_iam_role.lambda_worker_role.arn
  timeout = 60

  environment {
    variables = {
      EMAIL_SENDS_TABLE = aws_dynamodb_table.email_sends.name
    }
  }

  tags = {
    Project = "OmniProEmailServerless"
  }
}

# Event Source Mapping: Conectar SQS a Lambda Worker
resource "aws_lambda_event_source_mapping" "sqs_mapping" {
  event_source_arn = aws_sqs_queue.email_send_queue.arn
  function_name    = aws_lambda_function.email_sender_worker.arn
  batch_size       = 10 # Procesar hasta 10 mensajes a la vez
}
