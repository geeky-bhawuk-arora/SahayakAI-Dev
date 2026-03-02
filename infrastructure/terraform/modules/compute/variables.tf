# infrastructure/terraform/modules/compute/variables.tf

variable "environment" {
  description = "The environment for deployment (e.g., dev, prod)"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for Lambda VPC config"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs for Lambda VPC config"
  type        = list(string)
  default     = []
}

variable "lambda_sg_id" {
  description = "Security group ID for Lambda VPC config (alternative to security_group_ids)"
  type        = string
  default     = ""
}

variable "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  type        = string
}

variable "sessions_table_name" {
  description = "DynamoDB table name for sessions"
  type        = string
}

variable "users_table_name" {
  description = "DynamoDB table name for users"
  type        = string
}

variable "schemes_table_name" {
  description = "DynamoDB table name for schemes"
  type        = string
}

variable "rules_table_name" {
  description = "DynamoDB table name for rules"
  type        = string
  default     = ""
}

variable "audio_input_bucket" {
  description = "S3 bucket for audio input"
  type        = string
  default     = ""
}

variable "audio_output_bucket" {
  description = "S3 bucket for audio output"
  type        = string
  default     = ""
}

variable "event_bus_name" {
  description = "EventBridge bus name"
  type        = string
  default     = ""
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
}

variable "orchestrator_provisioned_concurrency" {
  description = "Provisioned concurrency for orchestrator lambda"
  type        = number
  default     = 0
}

variable "retrieval_provisioned_concurrency" {
  description = "Provisioned concurrency for retrieval lambda"
  type        = number
  default     = 0
}

variable "eligibility_provisioned_concurrency" {
  description = "Provisioned concurrency for eligibility lambda"
  type        = number
  default     = 0
}

variable "orchestrator_reserved_concurrency" {
  description = "Reserved concurrency for orchestrator lambda"
  type        = number
  default     = -1
}

variable "voice_service_reserved_concurrency" {
  description = "Reserved concurrency for voice service lambda"
  type        = number
  default     = -1
}
