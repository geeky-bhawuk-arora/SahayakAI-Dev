# infrastructure/terraform/modules/compute/outputs.tf

output "lambda_invoke_arns" {
  description = "A map of function names to their invoke ARNs for API Gateway integration"
  value       = { for k, v in aws_lambda_function.services : k => v.invoke_arn }
}

output "lambda_function_names" {
  description = "List of all lambda function names"
  value       = [for v in aws_lambda_function.services : v.function_name]
}

output "all_function_names" {
    description = "List of all lambda function names for observability"
    value       = [for k, v in aws_lambda_function.services : v.function_name]
}
