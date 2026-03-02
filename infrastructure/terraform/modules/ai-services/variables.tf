# infrastructure/terraform/modules/ai-services/variables.tf

variable "environment" {
  description = "The deployment environment (dev, prod, etc.)"
  type        = string
}

variable "kms_key_arn" {
  description = "The ARN of the KMS key used for encryption"
  type        = string
}

variable "create_transcribe_vocabulary" {
  description = "Whether to create a custom Transcribe vocabulary"
  type        = bool
  default     = false
}

variable "vocabulary_name" {
  description = "The name of the custom Transcribe vocabulary"
  type        = string
  default     = ""
}

variable "vocabulary_s3_key" {
  description = "The S3 key for the custom Transcribe vocabulary file"
  type        = string
  default     = ""
}

variable "polly_output_bucket" {
  description = "The S3 bucket ID where Polly should output audio files"
  type        = string
}
