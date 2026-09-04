output "api_service_uri" {
  description = "Restricted API URI; no public invoker binding is created."
  value       = var.deploy_services ? google_cloud_run_v2_service.api[0].uri : null
}

output "web_service_uri" {
  description = "Restricted Web URI; connect a deployment-owned identity-aware gateway."
  value       = var.deploy_services ? google_cloud_run_v2_service.web[0].uri : null
}

output "cloud_sql_instance_connection_name" {
  description = "Authoritative PostgreSQL connection identity."
  value       = google_sql_database_instance.primary.connection_name
}

output "runtime_secret_ids" {
  description = "Secret containers that require operator-supplied versions."
  value       = { for key, secret in google_secret_manager_secret.runtime : key => secret.secret_id }
}
