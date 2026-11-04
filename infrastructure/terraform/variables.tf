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

variable "deploy_app" {
  type    = bool
  default = false
}

variable "app_secret" {
  description = "Application key"
  type        = string
}


variable "image_name" {
  description = "Docker image name"
  type        = string
  default     = "fastapi-api"
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "1.0.0"
}

variable "db_name" {
  description = "Database name"
  type        = string
}


variable "db_admin" {
  description = "Database user"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
}

variable "access_token_expire_minutes" {
  description = "Tiempo en que expira el token"
  type        = string
}

variable "login_rate_limit_ip" {
  description = ""
  type        = string
}

variable "login_rate_limit_account" {
  description = ""
  type        = string
}

variable "login_rate_limit_window_seconds" {
  description = ""
  type        = string
}

variable "app_env" {
  description = ""
  type        = string
}

variable "password_reset_expire_minutes" {
  description = ""
  type        = string
}

variable "password_reset_url" {
  description = ""
  type        = string
}

variable "password_reset_request_limit_ip" {
  description = ""
  type        = string
}

variable "password_reset_request_limit_account" {
  description = ""
  type        = string
}

variable "password_reset_attempt_limit_ip" {
  description = ""
  type        = string
}

variable "password_reset_window_seconds" {
  description = ""
  type        = string
}

variable "refresh_token_expire_days" {
  description = ""
  type        = string
}