locals {
  required_services = toset([
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "iamcredentials.googleapis.com",
    "redis.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "servicenetworking.googleapis.com",
    "sqladmin.googleapis.com",
    "vpcaccess.googleapis.com",
  ])
  runtime_secret_ids = toset([
    "database-url",
    "oidc-public-key",
    "redis-url",
  ])
}

resource "google_project_service" "required" {
  for_each = local.required_services

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "private" {
  name                    = "${var.name_prefix}-network"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.required]
}

resource "google_compute_subnetwork" "private" {
  name          = "${var.name_prefix}-subnet"
  ip_cidr_range = var.network_cidr
  region        = var.region
  network       = google_compute_network.private.id
}

resource "google_compute_global_address" "service_range" {
  name          = "${var.name_prefix}-service-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.private.id
}

resource "google_service_networking_connection" "private" {
  network                 = google_compute_network.private.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.service_range.name]
}

resource "google_vpc_access_connector" "serverless" {
  name          = "${var.name_prefix}-connector"
  region        = var.region
  network       = google_compute_network.private.name
  ip_cidr_range = var.connector_cidr
  min_instances = 2
  max_instances = 3
}

resource "google_service_account" "api" {
  account_id   = "careloop-api"
  display_name = "CareLoop research API runtime"
}

resource "google_service_account" "web" {
  account_id   = "careloop-web"
  display_name = "CareLoop research Web runtime"
}

resource "google_service_account" "worker" {
  account_id   = "careloop-worker"
  display_name = "CareLoop research outbox worker"
}

resource "google_project_iam_member" "api_cloud_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "worker_cloud_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_secret_manager_secret" "runtime" {
  for_each = local.runtime_secret_ids

  secret_id = "${var.name_prefix}-${each.value}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_iam_member" "api_database" {
  secret_id = google_secret_manager_secret.runtime["database-url"].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "api_oidc" {
  secret_id = google_secret_manager_secret.runtime["oidc-public-key"].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "worker_database" {
  secret_id = google_secret_manager_secret.runtime["database-url"].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_secret_manager_secret_iam_member" "worker_redis" {
  secret_id = google_secret_manager_secret.runtime["redis-url"].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_sql_database_instance" "primary" {
  name                = "${var.name_prefix}-postgres"
  region              = var.region
  database_version    = "POSTGRES_17"
  deletion_protection = true

  settings {
    tier              = var.database_tier
    availability_type = "REGIONAL"
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.private.id
      enable_private_path_for_google_cloud_services = true
    }

    maintenance_window {
      day          = 7
      hour         = 7
      update_track = "stable"
    }
  }

  depends_on = [google_service_networking_connection.private]
}

resource "google_sql_database" "careloop" {
  name     = "careloop"
  instance = google_sql_database_instance.primary.name
}

resource "google_redis_instance" "ephemeral" {
  name                    = "${var.name_prefix}-redis"
  region                  = var.region
  tier                    = "STANDARD_HA"
  memory_size_gb          = var.redis_memory_size_gb
  redis_version           = "REDIS_7_2"
  authorized_network      = google_compute_network.private.id
  connect_mode            = "PRIVATE_SERVICE_ACCESS"
  transit_encryption_mode = "SERVER_AUTHENTICATION"
  auth_enabled            = true

  depends_on = [google_service_networking_connection.private]
}

resource "google_cloud_run_v2_service" "api" {
  count = var.deploy_services ? 1 : 0

  name                = "${var.name_prefix}-api"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  deletion_protection = true

  template {
    service_account = google_service_account.api.email

    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }

    vpc_access {
      connector = google_vpc_access_connector.serverless.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image   = var.api_image
      command = ["uv"]
      args = [
        "run",
        "--locked",
        "uvicorn",
        "careloop.web_api.production:create_production_app_from_environment",
        "--factory",
        "--host",
        "0.0.0.0",
        "--port",
        "8080",
      ]

      ports {
        container_port = 8080
      }

      env {
        name  = "CARELOOP_ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "CARELOOP_ENABLE_LOCAL_SYNTHETIC_IDENTITY"
        value = "false"
      }
      env {
        name  = "CARELOOP_REPOSITORY_ROOT"
        value = "/app"
      }
      env {
        name  = "CARELOOP_WEB_ORIGIN"
        value = var.web_origin
      }
      env {
        name  = "CARELOOP_OIDC_ISSUER"
        value = var.oidc_issuer
      }
      env {
        name  = "CARELOOP_OIDC_AUDIENCE"
        value = var.oidc_audience
      }
      env {
        name  = "CARELOOP_OIDC_ALGORITHM"
        value = "RS256"
      }
      env {
        name = "CARELOOP_DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.runtime["database-url"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "CARELOOP_OIDC_PUBLIC_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.runtime["oidc-public-key"].secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health/ready"
          port = 8080
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        failure_threshold     = 10
      }
    }
  }

  depends_on = [
    google_secret_manager_secret_iam_member.api_database,
    google_secret_manager_secret_iam_member.api_oidc,
    google_sql_database.careloop,
  ]
}

resource "google_cloud_run_v2_service" "web" {
  count = var.deploy_services ? 1 : 0

  name                = "${var.name_prefix}-web"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  deletion_protection = true

  template {
    service_account = google_service_account.web.email
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
    containers {
      image = var.web_image
      ports {
        container_port = 8080
      }
      env {
        name  = "PORT"
        value = "8080"
      }
    }
  }
}

resource "google_cloud_run_v2_worker_pool" "worker" {
  provider = google-beta
  count    = var.deploy_services ? 1 : 0

  name                = "${var.name_prefix}-worker"
  location            = var.region
  deletion_protection = true

  template {
    service_account = google_service_account.worker.email

    vpc_access {
      connector = google_vpc_access_connector.serverless.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image   = var.api_image
      command = ["uv"]
      args = [
        "run",
        "--locked",
        "arq",
        "careloop.web_api.worker.WorkerSettings",
      ]
      env {
        name  = "CARELOOP_ENVIRONMENT"
        value = "production"
      }
      env {
        name = "CARELOOP_DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.runtime["database-url"].secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "CARELOOP_REDIS_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.runtime["redis-url"].secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_secret_manager_secret_iam_member.worker_database,
    google_secret_manager_secret_iam_member.worker_redis,
    google_sql_database.careloop,
    google_redis_instance.ephemeral,
  ]
}
