# infrastructure/terraform/modules/ai-services/main.tf

resource "aws_transcribe_vocabulary" "custom_vocabulary" {
  count           = var.create_transcribe_vocabulary ? 1 : 0
  vocabulary_name = var.vocabulary_name
  language_code   = "en-IN" # Assuming Indian English given the domain
  
  # When using vocabulary_file_uri, it must point to an S3 object containing the list of words
  # Since the object key might be deployed separately or exist already, we point to it directly
  vocabulary_file_uri = "s3://${var.polly_output_bucket}/${var.vocabulary_s3_key}"

  tags = {
    Name        = "sahayak-${var.environment}-vocabulary"
    Environment = var.environment
  }
}
