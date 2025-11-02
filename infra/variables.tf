variable "aws_region" {
  description = "Región de AWS para desplegar los recursos"
  type        = string
  default     = "us-east-1"
}

variable "lambda_package_zip" {
  description = "Ruta al archivo ZIP de la función Lambda"
  type        = string
  default     = "../build/lambda_bundle.zip"
}
