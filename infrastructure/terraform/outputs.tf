output "resource_group_name" {
  description = "Name of the created resource group"
  value       = azurerm_resource_group.main.name
}

output "acr_name" {
  description = "Name Azure Container Registry (ACR)"
  value       = azurerm_container_registry.acr.name
}

output "acr_server" {
  description = "login server Azure Container Registry (ACR)"
  value       = azurerm_container_registry.acr.login_server
}

output "postgres_hostname" {
  description = "hostname postgres"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

# During the first stage, count = 0 and these outputs are null.
output "api_url" {
  description = "api url"
  value       = var.deploy_app ? "https://${azurerm_container_app.api[0].ingress[0].fqdn}" : null
}

output "swagger_url" {
  description = "swagger url"
  value       = var.deploy_app ? "https://${azurerm_container_app.api[0].ingress[0].fqdn}/docs" : null
}
