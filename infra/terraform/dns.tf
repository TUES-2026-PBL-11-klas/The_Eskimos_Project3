# DNS zone for the DO-delegated domain. Terraform owns every record. The apex (frontend) and
# `api` A-records are created only once `lb_ip` is known (second apply — see variables.tf).
resource "digitalocean_domain" "this" {
  name = var.domain
}

resource "digitalocean_record" "apex" {
  count  = var.lb_ip == "" ? 0 : 1
  domain = digitalocean_domain.this.id
  type   = "A"
  name   = "@"
  value  = var.lb_ip
  ttl    = 300
}

resource "digitalocean_record" "api" {
  count  = var.lb_ip == "" ? 0 : 1
  domain = digitalocean_domain.this.id
  type   = "A"
  name   = "api"
  value  = var.lb_ip
  ttl    = 300
}
