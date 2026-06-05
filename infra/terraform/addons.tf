# Platform add-ons as IaC (helm_release), not ad-hoc `helm install`. Resource requests are
# deliberately tiny to fit a single s-2vcpu-2gb node.
#
# NOTE: the cert-manager *ClusterIssuer* is intentionally NOT here. A kubernetes_manifest for a
# CRD installed in the same apply fails at plan time (the CRD doesn't exist yet). The ClusterIssuer
# ships in the application Helm chart instead (infra/helm/eventhub/templates/clusterissuer.yaml),
# which CD applies after cert-manager's CRDs exist.

# Populate the local Helm repo cache before any helm_release fetches a chart.
# The Terraform Helm provider delegates to the local helm binary, which needs the index files.
# Triggers re-run only when the set of repo URLs changes; helm repo add is idempotent.
resource "null_resource" "helm_repos" {
  triggers = {
    repos = sha256(join(",", [
      "https://bitnami-labs.github.io/sealed-secrets",
      "https://kubernetes.github.io/ingress-nginx",
      "https://charts.jetstack.io",
      "https://prometheus-community.github.io/helm-charts",
    ]))
  }

  provisioner "local-exec" {
    interpreter = ["powershell", "-Command"]
    command     = "helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets; helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx; helm repo add jetstack https://charts.jetstack.io; helm repo add prometheus-community https://prometheus-community.github.io/helm-charts; helm repo update"
  }
}

resource "helm_release" "sealed_secrets" {
  depends_on = [null_resource.helm_repos]

  name             = "sealed-secrets"
  repository       = "https://bitnami-labs.github.io/sealed-secrets"
  chart            = "sealed-secrets"
  version          = var.sealed_secrets_version
  namespace        = "kube-system"
  create_namespace = false

  # kubeseal defaults to controller name "sealed-secrets-controller" in kube-system.
  set {
    name  = "fullnameOverride"
    value = "sealed-secrets-controller"
  }
  set {
    name  = "resources.requests.cpu"
    value = "10m"
  }
  set {
    name  = "resources.requests.memory"
    value = "32Mi"
  }
}

resource "helm_release" "ingress_nginx" {
  depends_on = [null_resource.helm_repos, helm_release.kube_prometheus_stack]

  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = var.ingress_nginx_version
  namespace        = "ingress-nginx"
  create_namespace = true

  values = [yamlencode({
    controller = {
      replicaCount = 1
      resources    = { requests = { cpu = "50m", memory = "90Mi" } }
      service = {
        annotations = {
          "service.beta.kubernetes.io/do-loadbalancer-name" = "${var.cluster_name}-lb"
        }
      }
      metrics = {
        enabled        = true
        serviceMonitor = { enabled = true }
      }
    }
  })]
}

resource "helm_release" "cert_manager" {
  depends_on = [null_resource.helm_repos]

  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = var.cert_manager_version
  namespace        = "cert-manager"
  create_namespace = true

  set {
    name  = "crds.enabled"
    value = "true"
  }
  set {
    name  = "resources.requests.cpu"
    value = "10m"
  }
  set {
    name  = "resources.requests.memory"
    value = "32Mi"
  }
}

resource "helm_release" "kube_prometheus_stack" {
  depends_on = [null_resource.helm_repos]

  name             = "kube-prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = var.kube_prometheus_stack_version
  namespace        = "monitoring"
  create_namespace = true

  values = [yamlencode({
    # No Grafana, no Loki/Promtail — Prometheus + Alertmanager only (decision D5).
    grafana = { enabled = false }

    alertmanager = {
      alertmanagerSpec = {
        # Discover AlertmanagerConfig objects in any namespace (the app chart adds the Discord one).
        alertmanagerConfigSelectorNilUsesHelmValues = false
        alertmanagerConfigMatcherStrategy           = { type = "None" }
        resources                                   = { requests = { cpu = "10m", memory = "32Mi" } }
      }
    }

    prometheus = {
      prometheusSpec = {
        # Watch ServiceMonitors/PodMonitors/PrometheusRules cluster-wide, not just chart-labelled ones.
        serviceMonitorSelectorNilUsesHelmValues = false
        podMonitorSelectorNilUsesHelmValues     = false
        ruleSelectorNilUsesHelmValues           = false
        probeSelectorNilUsesHelmValues          = false
        retention                               = "2d"
        resources                               = { requests = { cpu = "50m", memory = "320Mi" } }
      }
    }

    "prometheus-node-exporter" = { resources = { requests = { cpu = "10m", memory = "16Mi" } } }
    "kube-state-metrics"       = { resources = { requests = { cpu = "10m", memory = "32Mi" } } }
  })]
}

resource "helm_release" "pushgateway" {
  name       = "prometheus-pushgateway"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus-pushgateway"
  version    = var.pushgateway_version
  namespace  = "monitoring"

  values = [yamlencode({
    resources      = { requests = { cpu = "10m", memory = "32Mi" } }
    serviceMonitor = { enabled = true }
  })]

  depends_on = [helm_release.kube_prometheus_stack]
}
