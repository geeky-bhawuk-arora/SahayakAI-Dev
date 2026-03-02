# infrastructure/terraform/modules/ai-services/outputs.tf

# If you create polly or bedrock related custom resources, output them here.
# For now, we only created transcribe vocabulary conditionally.

output "transcribe_vocabulary_name" {
  description = "Name of the custom transcribe vocabulary if created"
  value       = var.create_transcribe_vocabulary ? aws_transcribe_vocabulary.custom_vocabulary[0].vocabulary_name : null
}
