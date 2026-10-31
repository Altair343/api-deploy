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