{{- define "toil-wes.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- define "toil-wes.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else if contains (include "toil-wes.name" .) .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "toil-wes.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- define "toil-wes.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | quote }}
app.kubernetes.io/name: {{ include "toil-wes.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
{{- define "toil-wes.serviceAccountName" -}}
{{- default (include "toil-wes.fullname" .) .Values.serviceAccount.name -}}
{{- end -}}
{{- define "toil-wes.workerName" -}}
{{- printf "%s-celery" (include "toil-wes.fullname" . | trunc 56 | trimSuffix "-") -}}
{{- end -}}
{{- define "toil-wes.claimName" -}}
{{- printf "%s-shared" (include "toil-wes.fullname" . | trunc 56 | trimSuffix "-") -}}
{{- end -}}
{{- define "toil-wes.mounterName" -}}
{{- printf "%s-nfs-mounter" (include "toil-wes.fullname" . | trunc 51 | trimSuffix "-") -}}
{{- end -}}
{{- define "toil-wes.nfsName" -}}
{{- printf "%s-%s-nfs" .Release.Namespace (include "toil-wes.fullname" .) | trunc 253 | trimSuffix "-" -}}
{{- end -}}

{{- define "toil-wes.env" -}}
{{- if not (hasKey .Values.env "AWS_DEFAULT_REGION") }}
- name: AWS_DEFAULT_REGION
  value: {{ .Values.awsRegion | quote }}
{{- end }}
{{- if not (hasKey .Values.env "TOIL_APPLIANCE_SELF") }}
- name: TOIL_APPLIANCE_SELF
  value: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
{{- end }}
{{- if .Values.s3.host }}
{{- if not (hasKey .Values.env "AWS_ENDPOINT_URL") }}
- name: AWS_ENDPOINT_URL
  value: {{ printf "%s://%s:%s" (ternary "https" "http" .Values.s3.useSsl) .Values.s3.host .Values.s3.port | quote }}
{{- end }}
{{- if not (hasKey .Values.env "BOTO3_ENDPOINT_URL") }}
- name: BOTO3_ENDPOINT_URL
  value: {{ printf "%s://%s:%s" (ternary "https" "http" .Values.s3.useSsl) .Values.s3.host .Values.s3.port | quote }}
{{- end }}
{{- if not (hasKey .Values.env "TOIL_S3_HOST") }}
- name: TOIL_S3_HOST
  value: {{ .Values.s3.host | quote }}
{{- end }}
{{- if not (hasKey .Values.env "TOIL_S3_PORT") }}
- name: TOIL_S3_PORT
  value: {{ .Values.s3.port | quote }}
{{- end }}
{{- if not (hasKey .Values.env "TOIL_S3_USE_SSL") }}
- name: TOIL_S3_USE_SSL
  value: {{ ternary "True" "False" .Values.s3.useSsl | quote }}
{{- end }}
{{- end }}
{{- if .Values.celery.enabled }}
- name: TOIL_WES_BROKER_URL
  {{- if .Values.celery.brokerSecret.name }}
  valueFrom:
    secretKeyRef:
      name: {{ .Values.celery.brokerSecret.name | quote }}
      key: {{ .Values.celery.brokerSecret.key | quote }}
  {{- else }}
  value: {{ .Values.celery.brokerUrl | quote }}
  {{- end }}
- name: TOIL_WES_RESULT_BACKEND
  value: {{ .Values.celery.resultBackend | default "rpc://" | quote }}
{{- end }}
{{- if .Values.s3.credentialsSecret.name }}
- name: AWS_ACCESS_KEY_ID
  valueFrom:
    secretKeyRef:
      name: {{ .Values.s3.credentialsSecret.name | quote }}
      key: {{ .Values.s3.credentialsSecret.accessKeyKey | quote }}
- name: AWS_SECRET_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: {{ .Values.s3.credentialsSecret.name | quote }}
      key: {{ .Values.s3.credentialsSecret.secretKeyKey | quote }}
{{- end }}
{{- range $k, $v := .Values.env }}
- name: {{ $k }}
  value: {{ $v | quote }}
{{- end }}
{{- end -}}
