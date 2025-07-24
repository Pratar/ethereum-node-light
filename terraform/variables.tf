variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Google Cloud zone"
  type        = string
  default     = "us-central1-a"
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "ethereum-cluster"
}

variable "vpc_name" {
  description = "VPC network name"
  type        = string
  default     = "ethereum-vpc"
}

variable "subnet_name" {
  description = "Subnet name"
  type        = string
  default     = "ethereum-subnet"
}

variable "node_pool_name" {
  description = "Node pool name"
  type        = string
  default     = "ethereum-node-pool"
}

variable "storage_bucket_name" {
  description = "Storage bucket name"
  type        = string
  default     = "ethereum-data"
}

variable "gateway_api_channel" {
  description = "Gateway API channel (STANDARD or EXPERIMENTAL)"
  type        = string
  default     = "STANDARD"
  validation {
    condition     = contains(["STANDARD", "EXPERIMENTAL"], var.gateway_api_channel)
    error_message = "Gateway API channel must be either STANDARD or EXPERIMENTAL."
  }
} 