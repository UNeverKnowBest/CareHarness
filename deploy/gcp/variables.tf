variable "project_id" {
  description = "Dedicated GCP research project ID."
  type        = string
}

variable "region" {
  description = "Single GCP region for the removable research stack."
  type        = string
  default     = "us-central1"
}

variable "name_prefix" {
  description = "Prefix applied to non-global resources."
  type        = string
  default     = "careloop-research"
}

variable "api_image" {
  description = "Immutable digest-pinned API image built from docker/api.Dockerfile."
  type        = string
  default     = "us-docker.pkg.dev/replace-me/careloop/api@sha256:replace-me"
}

variable "web_image" {
  description = "Immutable digest-pinned Web image built with NEXT_PUBLIC_API_BASE."
  type        = string
  default     = "us-docker.pkg.dev/replace-me/careloop/web@sha256:replace-me"
}

variable "deploy_services" {
  description = "Enable only after secret versions and digest-pinned images exist."
  type        = bool
  default     = false
}

variable "web_origin" {
  description = "Exact HTTPS browser origin allowed by the API."
  type        = string
  default     = "https://research.example.invalid"

  validation {
    condition     = startswith(var.web_origin, "https://")
    error_message = "web_origin must use HTTPS."
  }
}

variable "oidc_issuer" {
  description = "Deployment-owned OIDC issuer; no local identity is allowed."
  type        = string
  default     = "https://identity.example.invalid"

  validation {
    condition     = startswith(var.oidc_issuer, "https://")
    error_message = "oidc_issuer must use HTTPS."
  }
}

variable "oidc_audience" {
  description = "Exact OIDC audience checked by the API adapter."
  type        = string
  default     = "careloop-research"
}

variable "network_cidr" {
  description = "Private application subnet CIDR."
  type        = string
  default     = "10.24.0.0/24"
}

variable "connector_cidr" {
  description = "Dedicated Serverless VPC Access connector CIDR."
  type        = string
  default     = "10.24.1.0/28"
}

variable "database_tier" {
  description = "Regional Cloud SQL machine tier selected by the operator."
  type        = string
  default     = "db-custom-2-7680"
}

variable "redis_memory_size_gb" {
  description = "Ephemeral Memorystore capacity; PostgreSQL remains authoritative."
  type        = number
  default     = 1

  validation {
    condition     = var.redis_memory_size_gb >= 1
    error_message = "redis_memory_size_gb must be at least 1."
  }
}
