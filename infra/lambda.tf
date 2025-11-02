resource "aws_lambda_function" "ingestor" {
  function_name = "email-ingestor-lambda"

  filename         = var.lambda_package_zip
  source_code_hash = filebase64sha256(var.lambda_package_zip)

  handler = "app.main.handler"
  runtime = "python3.12"
  role    = aws_iam_role.lambda_ingestor_role.arn
  timeout = 30

  environment {
    variables = {
      EMAIL_SENDS_TABLE = aws_dynamodb_table.email_sends.name
    }
  }

  tags = {
    Project = "OmniProEmailServerless"
  }
}
