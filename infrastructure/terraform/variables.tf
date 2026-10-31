variable "subscription_id" {
  description = "Azure subscription used to create resources."
  type        = string
}

variable "project_name" {
  description = "Project name."
  type        = string
  default     = "fastapi"
  validation {
    condition     = can(regex("^[a-z][a-z0-9]{2,11}$", var.project_name))
    error_message = "Usa de 3 a 12 caracteres: minúsculas y números; empieza con letra."
  }
}

variable "location" {
  description = "Region"
  type        = string
  default     = "eastus2"
}

variable "tags" {
  type = map(string)
  default = {
    project     = "fastapi"
    environment = "portfolio"
    managed_by  = "terraform"
  }
}
