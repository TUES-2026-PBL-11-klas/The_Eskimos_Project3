# ── Providers ────────────────────────────────────────────────────────────────────────────────
provider "digitalocean" {
  token = var.do_token
}

# The kubernetes/helm providers talk to the cluster created below. The kubeconfig token DOKS
# returns is short-lived, which is fine for an apply; if a later apply fails to auth, re-run.
provider "kubernetes" {
  host                   = digitalocean_kubernetes_cluster.this.endpoint
  token                  = digitalocean_kubernetes_cluster.this.kube_config[0].token
  cluster_ca_certificate = base64decode(digitalocean_kubernetes_cluster.this.kube_config[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = digitalocean_kubernetes_cluster.this.endpoint
    token                  = digitalocean_kubernetes_cluster.this.kube_config[0].token
    cluster_ca_certificate = base64decode(digitalocean_kubernetes_cluster.this.kube_config[0].cluster_ca_certificate)
  }
}

# ── Networking ───────────────────────────────────────────────────────────────────────────────
resource "digitalocean_vpc" "this" {
  name     = "${var.cluster_name}-vpc"
  region   = var.region
  ip_range = var.vpc_ip_range
}

# ── Cluster ──────────────────────────────────────────────────────────────────────────────────
data "digitalocean_kubernetes_versions" "this" {
  version_prefix = var.k8s_version_prefix
}

resource "digitalocean_kubernetes_cluster" "this" {
  name     = var.cluster_name
  region   = var.region
  version  = data.digitalocean_kubernetes_versions.this.latest_version
  vpc_uuid = digitalocean_vpc.this.id

  node_pool {
    name       = "${var.cluster_name}-pool"
    size       = var.node_size
    node_count = var.node_count
    tags       = [digitalocean_tag.node.name]
  }
}

# DO requires a tag to exist as its own resource before a firewall can target it.
resource "digitalocean_tag" "node" {
  name = "eventhub-worker"
}

# ── Firewall (scoped to the worker node pool tag) ────────────────────────────────────────────
# DOKS also manages a baseline firewall; this layer documents the intended posture and is
# permissive enough not to interfere with the managed LoadBalancer health checks (nodeports).
resource "digitalocean_firewall" "nodes" {
  name       = "${var.cluster_name}-nodes"
  tags       = [digitalocean_tag.node.name]
  depends_on = [digitalocean_kubernetes_cluster.this]

  # All intra-VPC traffic (pod/node/control-plane chatter).
  inbound_rule {
    protocol         = "tcp"
    port_range       = "1-65535"
    source_addresses = [digitalocean_vpc.this.ip_range]
  }
  inbound_rule {
    protocol         = "udp"
    port_range       = "1-65535"
    source_addresses = [digitalocean_vpc.this.ip_range]
  }
  # Public HTTP/HTTPS to the ingress controller.
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  # NodePort range — the DO LoadBalancer forwards to these and runs health checks here.
  inbound_rule {
    protocol         = "tcp"
    port_range       = "30000-32767"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  inbound_rule {
    protocol         = "icmp"
    source_addresses = [digitalocean_vpc.this.ip_range]
  }

  # Egress: unrestricted (image pulls from GHCR, ACME, scraping target sites).
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
