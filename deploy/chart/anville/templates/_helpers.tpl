{{/* ✨ Labels every object carries. */}}
{{- define "anville.labels" -}}
app.kubernetes.io/name: anville
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
anville/tier: {{ .Values.tier }}
{{- end }}

{{/* ✨ What selects one component's pods: web, postgres or backup. Call with (list . "web"). */}}
{{- define "anville.selector" -}}
app.kubernetes.io/name: anville
app.kubernetes.io/instance: {{ (index . 0).Release.Name }}
app.kubernetes.io/component: {{ index . 1 }}
{{- end }}

{{/* ✨ The image, always by digest. */}}
{{- define "anville.image" -}}
{{ .Values.image.repository }}@{{ required "image.digest is required: an environment runs a digest, never a tag" .Values.image.digest }}
{{- end }}

{{/* ✨ The Host header Django will accept. Without a hostname only a port-forward reaches the pod. */}}
{{- define "anville.host" -}}
{{ .Values.hostname | default "localhost" }}
{{- end }}

{{/*
✨ The database connection, for the web pod, its migration and the backup alike.

In-cluster, the URL is put together from the password in the Secret. Kubernetes fills in $(POSTGRES_PASSWORD)
from the variable before it, so the password must be safe inside a URL: letters, digits, - and _ only.
*/}}
{{- define "anville.databaseEnv" -}}
{{- if .Values.postgres.enabled }}
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.secretName }}
      key: POSTGRES_PASSWORD
- name: DATABASE_URL
  value: postgres://anville:$(POSTGRES_PASSWORD)@{{ .Release.Name }}-postgres:5432/anville
{{- else }}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.secretName }}
      key: DATABASE_URL
{{- end }}
{{- end }}

{{/* ✨ Everything Django reads from the environment (the README lists the variables). */}}
{{- define "anville.djangoEnv" -}}
- name: DJANGO_DEBUG
  value: "false"
- name: DJANGO_ALLOWED_HOSTS
  value: {{ include "anville.host" . | quote }}
{{- if .Values.hostname }}
- name: DJANGO_HTTPS
  value: "true"
- name: DJANGO_HSTS_SECONDS
  value: {{ .Values.web.hstsSeconds | quote }}
{{- end }}
- name: DATABASE_CONN_MAX_AGE
  value: {{ .Values.web.connMaxAge | quote }}
- name: WEB_CONCURRENCY
  value: {{ .Values.web.workers | quote }}
{{- with .Values.email.from }}
- name: DEFAULT_FROM_EMAIL
  value: {{ . | quote }}
{{- end }}
{{- if eq .Values.tier "staging" }}
- name: ANVILLE_EMAIL_DISCLAIMER
  value: {{ required "email.disclaimer cannot be empty on a staging environment: its email must say it is from a test system" .Values.email.disclaimer | quote }}
{{- end }}
- name: DJANGO_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ .Values.secretName }}
      key: DJANGO_SECRET_KEY
- name: ANVILLE_ENROLMENT_REQUIRED
  value: {{ .Values.enrolment.required | quote }}
{{- if .Values.enrolment.required }}
- name: ANVILLE_ENROLMENT_CODE
  valueFrom:
    secretKeyRef:
      name: {{ .Values.secretName }}
      key: ANVILLE_ENROLMENT_CODE
{{- end }}
- name: EMAIL_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.secretName }}
      key: EMAIL_URL
      optional: true
{{ include "anville.databaseEnv" . | trim }}
{{- end }}

{{/* ✨ No privileges, and nothing written to the image's own filesystem. */}}
{{- define "anville.containerSecurity" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop: ["ALL"]
{{- end }}
