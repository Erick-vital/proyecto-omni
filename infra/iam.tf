resource "aws_iam_role" "lambda_ingestor_role" {
  name = "lambda-ingestor-role"

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

resource "aws_iam_policy" "lambda_ingestor_policy" {
  name        = "lambda-ingestor-policy"
  description = "Permisos mínimos para Lambda ingestor (DynamoDB + logs)"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoWrite",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
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
    },
    {
      "Sid": "SQSSend",
      "Effect": "Allow",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.email_send_queue.arn}"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_ingestor_role_attach" {
  role       = aws_iam_role.lambda_ingestor_role.name
  policy_arn = aws_iam_policy.lambda_ingestor_policy.arn
}
