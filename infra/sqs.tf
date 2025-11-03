
resource "aws_sqs_queue" "email_send_dlq" {
  name = "email_send_dlq"
  tags = {
    Project = "OmniProEmailServerless"
  }
}

resource "aws_sqs_queue" "email_send_queue" {
  name = "email_send_queue"
  visibility_timeout_seconds = 65 # Debe ser >= al timeout de la Lambda worker
  # If a message fails to process 3 times, send it to the DLQ
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.email_send_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project = "OmniProEmailServerless"
  }
}
