{{/* Base name — release name unless overridden. Install as `eventhub` for stable resource names. */}}
{{- define "eventhub.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/* Common labels. */}}
{{- define "eventhub.labels" -}}
app.kubernetes.io/part-of: eventhub
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{/* Per-component selector labels. Call with (dict "ctx" . "component" "api"). */}}
{{- define "eventhub.selectorLabels" -}}
app.kubernetes.io/name: eventhub-{{ .component }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
{{- end -}}

{{/* Fully-qualified image ref. Call with (dict "ctx" . "svc" "api"). */}}
{{- define "eventhub.image" -}}
{{- $img := .ctx.Values.image -}}
{{- printf "%s/%s/eventhub-%s:%s" $img.registry $img.owner .svc ($img.tag | toString) -}}
{{- end -}}

{{/* Stable Postgres service host (matches the sealed *_DB_URL values). */}}
{{- define "eventhub.postgresHost" -}}
{{- printf "%s-postgres" (include "eventhub.fullname" .) -}}
{{- end -}}
