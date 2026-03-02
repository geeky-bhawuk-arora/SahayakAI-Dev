# infrastructure/terraform/modules/compute/main.tf

# Dummy payload for initial lambda creation before CD pipeline updates it
data "archive_file" "dummy" {
  type        = "zip"
  output_path = "${path.module}/dummy.zip"

  source {
    content  = "def lambda_handler(event, context):\n  return 'dummy'"
    filename = "lambda_function.py"
  }
}

locals {
  sg_ids = length(var.security_group_ids) > 0 ? var.security_group_ids : (var.lambda_sg_id != "" ? [var.lambda_sg_id] : [])

  lambdas = {
    "voice-service" = {
      description = "Handles Voice to Text and Text to Voice conversions"
      timeout     = 10
      memory      = 256
      role        = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/sahayak-${var.environment}-voice-role"
    },
    "conversation-orchestrator" = {
      description = "Core RAG orchestrator interacting with Bedrock"
      timeout     = 30
      memory      = 512
      role        = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/sahayak-${var.environment}-orchestrator-role"
    },
    "scheme-retrieval-service" = {
      description = "Retrieves relevant schemes from OpenSearch"
      timeout     = 15
      memory      = 256
      role        = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/sahayak-${var.environment}-orchestrator-role"
    },
    "eligibility-engine" = {
      description = "Evaluates citizen eligibility against schemes"
      timeout     = 10
      memory      = 256
      role        = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/sahayak-${var.environment}-orchestrator-role"
    },
    "user-profile-service" = {
      description = "Manages citizen profiles and session history"
      timeout     = 5
      memory      = 128
      role        = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/sahayak-${var.environment}-orchestrator-role"
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each          = local.lambdas
  name              = "/aws/lambda/sahayak-${var.environment}-${each.key}"
  retention_in_days = 14
  kms_key_id        = var.kms_key_arn
  
  tags = {
    Environment = var.environment
    Service     = each.key
  }
}

resource "aws_lambda_function" "services" {
  for_each = local.lambdas

  function_name = "sahayak-${var.environment}-${each.key}"
  description   = each.value.description
  role          = each.value.role
  handler       = "src.main.lambda_handler"
  runtime       = "python3.11"
  timeout       = each.value.timeout
  memory_size   = each.value.memory

  filename         = data.archive_file.dummy.output_path
  source_code_hash = data.archive_file.dummy.output_base64sha256

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = local.sg_ids
  }

  environment {
    variables = {
      ENVIRONMENT           = var.environment
      OPENSEARCH_ENDPOINT   = var.opensearch_endpoint
      SESSIONS_TABLE_NAME   = var.sessions_table_name
      USERS_TABLE_NAME      = var.users_table_name
      SCHEMES_TABLE_NAME    = var.schemes_table_name
      RULES_TABLE_NAME      = var.rules_table_name
      AUDIO_INPUT_BUCKET    = var.audio_input_bucket
      AUDIO_OUTPUT_BUCKET   = var.audio_output_bucket
      EVENT_BUS_NAME        = var.event_bus_name
      KMS_KEY_ARN           = var.kms_key_arn
    }
  }

  tracing_config {
    mode = "Active"
  }

  # Ignore changes pushed by CD pipeline
  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash,
      version,
      last_modified,
      qualified_arn,
      qualified_invoke_arn
    ]
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

# Concurrency configurations (optional)
resource "aws_lambda_provisioned_concurrency_config" "orchestrator" {
  count                             = var.orchestrator_provisioned_concurrency > 0 ? 1 : 0
  function_name                     = aws_lambda_function.services["conversation-orchestrator"].function_name
  provisioned_concurrent_executions = var.orchestrator_provisioned_concurrency
  qualifier                         = aws_lambda_function.services["conversation-orchestrator"].version
  
  lifecycle { ignore_changes = [qualifier] }
}

resource "aws_lambda_provisioned_concurrency_config" "retrieval" {
  count                             = var.retrieval_provisioned_concurrency > 0 ? 1 : 0
  function_name                     = aws_lambda_function.services["scheme-retrieval-service"].function_name
  provisioned_concurrent_executions = var.retrieval_provisioned_concurrency
  qualifier                         = aws_lambda_function.services["scheme-retrieval-service"].version
  
  lifecycle { ignore_changes = [qualifier] }
}

resource "aws_lambda_provisioned_concurrency_config" "eligibility" {
  count                             = var.eligibility_provisioned_concurrency > 0 ? 1 : 0
  function_name                     = aws_lambda_function.services["eligibility-engine"].function_name
  provisioned_concurrent_executions = var.eligibility_provisioned_concurrency
  qualifier                         = aws_lambda_function.services["eligibility-engine"].version
  
  lifecycle { ignore_changes = [qualifier] }
}
