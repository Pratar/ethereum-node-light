terraform {
  required_version = ">= 1.12.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.44.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Enable APIs
resource "google_project_service" "compute" {
  project = var.project_id
  service = "compute.googleapis.com"
}

resource "google_project_service" "container" {
  project = var.project_id
  service = "container.googleapis.com"
  depends_on = [google_project_service.compute]
}

resource "google_project_service" "storage" {
  project = var.project_id
  service = "storage.googleapis.com"
  depends_on = [google_project_service.compute]
}

resource "google_project_service" "monitoring" {
  project = var.project_id
  service = "monitoring.googleapis.com"
  depends_on = [google_project_service.compute]
}

resource "google_project_service" "logging" {
  project = var.project_id
  service = "logging.googleapis.com"
  depends_on = [google_project_service.compute]
}

# VPC
resource "google_compute_network" "vpc" {
  name                    = var.vpc_name
  auto_create_subnetworks = false
  depends_on = [google_project_service.compute]
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = var.subnet_name
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  
  # Enable flow logs for monitoring
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling       = 0.5
    metadata            = "INCLUDE_ALL_METADATA"
  }
}

# Firewall rules
resource "google_compute_firewall" "allow_ethereum_p2p" {
  name    = "allow-ethereum-p2p"
  network = google_compute_network.vpc.name
  
  allow {
    protocol = "tcp"
    ports    = ["30303"]
  }
  
  allow {
    protocol = "udp"
    ports    = ["30303"]
  }
  
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ethereum-node"]
}

resource "google_compute_firewall" "allow_ethereum_rpc" {
  name    = "allow-ethereum-rpc"
  network = google_compute_network.vpc.name
  
  allow {
    protocol = "tcp"
    ports    = ["8545", "8546"]
  }
  
  source_ranges = ["10.0.0.0/24"]
  target_tags   = ["ethereum-node"]
}

# GKE Cluster с расширенными настройками
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region
  
  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = false
  
  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name
  
  ip_allocation_policy {
    cluster_ipv4_cidr_block  = "172.16.0.0/16"
    services_ipv4_cidr_block = "172.17.0.0/16"
  }
  
  # Настройки безопасности
  enable_shielded_nodes = true
  
  # Настройки сети
  network_policy {
    enabled  = true
    provider = "CALICO"
  }
  
  # Gateway API v1 будет включен через gcloud команду после создания кластера
  
  # Настройки узлов
  node_config {
    machine_type = "e2-standard-4"  # Увеличиваем ресурсы
    disk_size_gb = 100              # Увеличиваем диск
    
    # Теги для firewall
    tags = ["ethereum-node"]
    
    oauth_scopes = [
      "https://www.googleapis.com/auth/compute",
      "https://www.googleapis.com/auth/devstorage.read_write",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring"
    ]
  }
  
  depends_on = [google_project_service.container]
}

# Включение Gateway API v1 через gcloud команду
resource "null_resource" "enable_gateway_api" {
  provisioner "local-exec" {
    command = "gcloud container clusters update ${google_container_cluster.primary.name} --region=${var.region} --gateway-api=standard"
  }
  
  depends_on = [google_container_cluster.primary]
  
  # Триггер при изменении кластера
  triggers = {
    cluster_name = google_container_cluster.primary.name
    region       = var.region
    project_id   = var.project_id
  }
}

# Node Pool с увеличенными ресурсами
resource "google_container_node_pool" "primary_nodes" {
  name       = var.node_pool_name
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = 1
  
  # Автоматическое масштабирование
  autoscaling {
    min_node_count = 1
    max_node_count = 3
  }
  
  # Настройки обновления
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  
  node_config {
    machine_type = "e2-standard-4"  # 4 vCPU, 16 GB RAM
    disk_size_gb = 100
    
    # Теги для firewall
    tags = ["ethereum-node"]
    
    oauth_scopes = [
      "https://www.googleapis.com/auth/compute",
      "https://www.googleapis.com/auth/devstorage.read_write",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring"
    ]
    

    
    # Настройки метаданных
    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

# Storage Bucket для данных Ethereum
resource "google_storage_bucket" "ethereum_data" {
  name          = "${var.storage_bucket_name}-${var.project_id}"
  location      = var.region
  force_destroy = true
  
  # Настройки версионирования
  versioning {
    enabled = true
  }
  
  # Настройки жизненного цикла
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
  
  # Настройки безопасности
  uniform_bucket_level_access = true
  
  depends_on = [google_project_service.storage]
}

# Cloud Armor для защиты от DDoS (упрощенная версия)
resource "google_compute_security_policy" "ethereum_policy" {
  name = "ethereum-security-policy"
  
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}

# Outputs
output "cluster_name" {
  value = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  value = google_container_cluster.primary.endpoint
}

output "storage_bucket_name" {
  value = google_storage_bucket.ethereum_data.name
}

output "vpc_name" {
  value = google_compute_network.vpc.name
}

output "subnet_name" {
  value = google_compute_subnetwork.subnet.name
}

 