# Suffix for globally unique names (ACR y PostgreSQL).
resource "random_string" "suffix" {
  upper   = false
  special = false
  length  = 6
}

# Create a resource group
resource "azurerm_resource_group" "main" {
  name     = "${var.project_name}-rg"
  location = var.location
  tags     = var.tags
}

# Create a network
resource "azurerm_virtual_network" "main" {
  name                = "${var.project_name}-vnet"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = ["10.0.0.0/16"]
}

# Subnet for Container Apps
resource "azurerm_subnet" "container_apps" {
  name                 = "container-apps-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.0.0/27"]

  delegation {
    name = "container-apps-delegation"
    service_delegation {
      name = "Microsoft.App/environments"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }
}

# Subnet for PostgreSQL
resource "azurerm_subnet" "postgres" {
  name                 = "postgres-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name

  address_prefixes = ["10.0.1.0/28"]

  delegation {
    name = "postgres-delegation"

    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"

      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }
}

# Private DNS for PostgreSQL
resource "azurerm_private_dns_zone" "postgres" {
  name                = "${var.project_name}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                = "${var.project_name}-dns-link"
  private_dns_zone_id = azurerm_private_dns_zone.postgres.id
  virtual_network_id  = azurerm_virtual_network.main.id
}

# Create server postgresql
resource "azurerm_postgresql_flexible_server" "main" {
  name = "${var.project_name}-pg-${random_string.suffix.result}"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  version             = "17"

  administrator_login    = var.db_admin
  administrator_password = var.db_password

  sku_name   = "B_Standard_B1ms"
  storage_mb = 32768

  backup_retention_days        = 7
  geo_redundant_backup_enabled = false

  delegated_subnet_id           = azurerm_subnet.postgres.id
  private_dns_zone_id           = azurerm_private_dns_zone.postgres.id
  public_network_access_enabled = false

  authentication {
    active_directory_auth_enabled = true
    password_auth_enabled         = true
  }

  depends_on = [
    azurerm_private_dns_zone_virtual_network_link.postgres
  ]
  tags = var.tags
}

# Create database
resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.db_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"

  # prevent the possibility of accidental data loss
  lifecycle {
    prevent_destroy = true
  }
}

# Redis
resource "azurerm_managed_redis" "main" {
  name                      = "${var.project_name}-redis-${random_string.suffix.result}"
  resource_group_name       = azurerm_resource_group.main.name
  location                  = azurerm_resource_group.main.location
  sku_name                  = "Balanced_B0"
  high_availability_enabled = false
  public_network_access     = "Enabled"

  default_database {
    access_keys_authentication_enabled = true
    client_protocol                    = "Encrypted"
    clustering_policy                  = "OSSCluster"
    eviction_policy                    = "VolatileLRU"
  }

  tags = var.tags
}

# Azure Container Registry (ACR). A private repository for storing Docker images.
resource "azurerm_container_registry" "acr" {
  name                = "${var.project_name}${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = var.tags
}

# A managed identity that can be granted permissions on other resources.
resource "azurerm_user_assigned_identity" "container_app" {
  name                = "${var.project_name}-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = var.tags
}

# Permission to download images from the ACR
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.container_app.principal_id
}

# A Container Apps Environment groups together the applications that will run in the same environment.
resource "azurerm_container_app_environment" "main" {
  name                     = "${var.project_name}-environment"
  location                 = azurerm_resource_group.main.location
  resource_group_name      = azurerm_resource_group.main.name
  infrastructure_subnet_id = azurerm_subnet.container_apps.id
  zone_redundancy_enabled  = false
  # logs_destination = "azure-monitor"

  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }

  tags = var.tags
}

# Azure Container App
resource "azurerm_container_app" "api" {
  # Allows for the creation—or non-creation—of the application.
  count                        = var.deploy_app ? 1 : 0
  name                         = "${var.project_name}-api"
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"
  workload_profile_name        = "Consumption"

  # They assign the managed identity to the application and indicate
  # that it should be used to authenticate with ACR.
  identity {
    type = "UserAssigned"

    identity_ids = [
      azurerm_user_assigned_identity.container_app.id
    ]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.container_app.id
  }


  secret {
    name  = "database-url"
    value = "postgresql://${var.db_admin}:${var.db_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${var.db_name}?sslmode=require"
  }

  template {
    min_replicas = 0
    max_replicas = 1

    http_scale_rule {
      name                = "http-scale"
      concurrent_requests = "10"
    }

    container {
      name   = "fastapi"
      image  = "${azurerm_container_registry.acr.login_server}/${var.image_name}:${var.image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "APP_NAME"
        value = var.project_name
      }
      env {
        name  = "APP_VERSION"
        value = var.image_tag
      }
      env {
        name  = "DEBUG"
        value = "false"
      }
      env {
        name  = "ACCESS_TOKEN_EXPIRE_MINUTES"
        value = var.access_token_expire_minutes
      }
      env {
        name  = "DB_HOST"
        value = azurerm_postgresql_flexible_server.main.fqdn
      }
      env {
        name  = "DB_PORT"
        value = 5432
      }
      env {
        name  = "DB_NAME"
        value = var.db_name
      }
      env {
        name  = "DB_USER"
        value = var.db_admin
      }
      env {
        name  = "DB_PASSWORD"
        value = var.db_password
      }
      env {
        name  = "REDIS_HOST"
        value = azurerm_managed_redis.main.hostname
      }
      env {
        name  = "REDIS_PORT"
        value = azurerm_managed_redis.main.default_database[0].port
      }
      env {
        name  = "REDIS_PASSWORD"
        value = azurerm_managed_redis.main.default_database[0].primary_access_key
      }
      env {
        name  = "LOGIN_RATE_LIMIT_IP"
        value = var.login_rate_limit_ip
      }
      env {
        name  = "LOGIN_RATE_LIMIT_ACCOUNT"
        value = var.login_rate_limit_account
      }
      env {
        name  = "LOGIN_RATE_LIMIT_WINDOW_SECONDS"
        value = var.login_rate_limit_window_seconds
      }
      env {
        name  = "APP_ENV"
        value = var.app_env
      }
      env {
        name  = "PASSWORD_RESET_EXPIRE_MINUTES"
        value = var.password_reset_expire_minutes
      }
      env {
        name  = "PASSWORD_RESET_URL"
        value = var.password_reset_url
      }
      env {
        name  = "PASSWORD_RESET_REQUEST_LIMIT_IP"
        value = var.password_reset_request_limit_ip
      }
      env {
        name  = "PASSWORD_RESET_REQUEST_LIMIT_ACCOUNT"
        value = var.password_reset_request_limit_account
      }
      env {
        name  = "PASSWORD_RESET_ATTEMPT_LIMIT_IP"
        value = var.password_reset_attempt_limit_ip
      }
      env {
        name  = "PASSWORD_RESET_WINDOW_SECONDS"
        value = var.password_reset_window_seconds
      }
      env {
        name  = "REFRESH_TOKEN_EXPIRE_DAYS"
        value = var.refresh_token_expire_days
      }
      env {
        name        = "SECRET_KEY"
        secret_name = var.app_secret
      }
    }
  }

  # Expose api publicly.
  ingress {
    external_enabled           = true
    target_port                = 8000
    transport                  = "auto"
    allow_insecure_connections = false

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  depends_on = [
    azurerm_role_assignment.acr_pull,
    azurerm_postgresql_flexible_server_database.main
  ]
  tags = var.tags
}
