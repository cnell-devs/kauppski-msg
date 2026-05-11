variable "supabase_url" {
  description = "Supabase project URL used to fetch JWKS for JWT verification"
  type        = string
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
