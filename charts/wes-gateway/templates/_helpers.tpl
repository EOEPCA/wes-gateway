{{- define "wes-gateway.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- define "wes-gateway.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 50 | trimSuffix "-" -}}
{{- else if eq .Release.Name (include "wes-gateway.name" .) -}}
{{- .Release.Name | trunc 50 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "wes-gateway.name" .) | trunc 50 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- define "wes-gateway.selectorLabels" -}}
app.kubernetes.io/name: {{ include "wes-gateway.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- define "wes-gateway.labels" -}}
{{ include "wes-gateway.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | quote }}
{{- end -}}
{{- define "wes-gateway.serviceAccount" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "wes-gateway.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
{{- define "wes-gateway.registry" -}}
{{- if .Values.backendConfig -}}
{{- .Values.backendConfig -}}
{{- else -}}
{{- toYaml .Values.registry -}}
{{- end -}}
{{- end -}}
