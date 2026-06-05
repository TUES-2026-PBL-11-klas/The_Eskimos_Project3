variable "do_token" {
  description = "DigitalOcean API token (read+write). Provide via TF_VAR_do_token; never commit it."
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean region slug for the cluster and load balancer."
  type        = string
  default     = "fra1"
}

variable "cluster_name" {
  description = "Name of the DOKS cluster."
  type        = string
  default     = "eventhub-doks"
}

variable "k8s_version_prefix" {
  description = "Match the latest available DOKS patch for this minor version (>= 1.30 required)."
  type        = string
  default     = "1.3"
}

variable "node_size" {
  description = "Droplet size slug for the single worker node pool."
  type        = string
  default     = "s-2vcpu-2gb"
}

variable "node_count" {
  description = "Number of worker nodes."
  type        = number
  default     = 1
}

variable "vpc_ip_range" {
  description = "Private CIDR for the cluster VPC."
  type        = string
  default     = "10.116.0.0/20"
}

variable "domain" {
  description = "Apex domain delegated to DigitalOcean (e.g. eventhub.example.com)."
  type        = string
}

variable "lb_ip" {
  description = <<-EOT
    Public IP of the ingress-nginx LoadBalancer. Leave empty on the first apply (cluster +
    add-ons + DNS zone are created), then read it from `kubectl get svc -n ingress-nginx`,
    set this, and re-apply to create the apex/api A-records.
  EOT
  type        = string
  default     = ""
}

variable "acme_email" {
  description = "Contact email for Let's Encrypt registration (cert-manager ClusterIssuer)."
  type        = string
}

# --- Pinned add-on chart versions (keep these explicit so cluster state is reproducible) ---

variable "sealed_secrets_version" {
  description = "sealed-secrets Helm chart version."
  type        = string
  default     = "2.16.1"
}

variable "ingress_nginx_version" {
  description = "ingress-nginx Helm chart version."
  type        = string
  default     = "4.11.3"
}

variable "cert_manager_version" {
  description = "cert-manager Helm chart version."
  type        = string
  default     = "v1.16.2"
}

variable "kube_prometheus_stack_version" {
  description = "kube-prometheus-stack Helm chart version."
  type        = string
  default     = "65.5.1"
}

variable "pushgateway_version" {
  description = "prometheus-pushgateway Helm chart version."
  type        = string
  default     = "2.15.0"
}
