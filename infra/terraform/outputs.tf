output "cluster_name" {
  description = "DOKS cluster name (use with: doctl kubernetes cluster kubeconfig save <name>)."
  value       = digitalocean_kubernetes_cluster.this.name
}

output "cluster_id" {
  value = digitalocean_kubernetes_cluster.this.id
}

output "cluster_endpoint" {
  value     = digitalocean_kubernetes_cluster.this.endpoint
  sensitive = true
}

output "domain_nameservers" {
  description = "Point the registrar (Namecheap) at these (they are always the DO three)."
  value       = ["ns1.digitalocean.com", "ns2.digitalocean.com", "ns3.digitalocean.com"]
}

output "lb_ip_hint" {
  description = "After the first apply, read the LB IP and set var.lb_ip, then re-apply for DNS."
  value       = "kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
}

output "app_urls" {
  description = "Where the app will be reachable once DNS + TLS are up."
  value = {
    frontend = "https://${var.domain}"
    api      = "https://api.${var.domain}"
  }
}
