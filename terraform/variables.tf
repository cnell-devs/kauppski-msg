variable "supabase_jwt_secret" {
  description = "Supabase JWT secret used to validate WebSocket auth tokens"
  type        = string
  sensitive   = true
}

variable "app_name" {
  description = "Prefix for all resource names"
  type        = string
  default     = "kauppski"
}

variable "env" {
  description = "Deployed resoure environment"
  type        = string
  default     = "dev"
}
