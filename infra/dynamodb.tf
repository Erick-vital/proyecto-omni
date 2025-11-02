resource "aws_dynamodb_table" "email_sends" {
  name         = "EmailSends"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "batch_id"
  range_key = "send_id"

  attribute {
    name = "batch_id"
    type = "S"
  }

  attribute {
    name = "send_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  # Índice Secundario Global (GSI)
  global_secondary_index {
    name            = "status_index"
    hash_key        = "status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  tags = {
    Project = "OmniProEmailServerless"
  }
}