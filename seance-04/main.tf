# main.tf — version paramétrée
# ─────────────────────────────

terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "anfa_net" {
  name = "anfa-network"
}

resource "docker_volume" "minio_data" {
  name = "anfa-minio-data-tf"
}

resource "docker_image" "minio" {
  name = "minio/minio:latest"
}

resource "docker_container" "minio" {
  name    = var.container_name # ← utilise la variable
  image   = docker_image.minio.image_id
  command = ["server", "/data", "--console-address", ":9001"]
  restart = "unless-stopped"

  ports {
    internal = 9000
    external = var.minio_api_port # ← utilise la variable
  }

  ports {
    internal = 9001
    external = var.minio_console_port # ← utilise la variable
  }

  env = [
    "MINIO_ROOT_USER=${var.minio_root_user}", # ← interpolation
    "MINIO_ROOT_PASSWORD=${var.minio_root_password}",
  ]

  volumes {
    volume_name    = docker_volume.minio_data.name
    container_path = "/data"
  }

  networks_advanced {
    name = docker_network.anfa_net.name
  }

  # Le moteur Docker injecte des options de log par défaut absentes du code.
  # Sans cette ligne, Terraform recréerait le conteneur à chaque plan
  # (l'idempotence serait cassée). On ignore donc ce champ géré par le moteur.
  lifecycle {
    ignore_changes = [log_opts]
  }
}
