# syntax=docker/dockerfile:1

# Copyright (C) New Community Church SE London 2026.
# For licensing information see LICENSE.md

# ✨ The one image every environment runs (docs/server-approach.md, section 3). It is public, so nothing may go
# into it that the repository does not already publish: Dockerfile.dockerignore admits only what is copied
# below. That file is named for this Dockerfile, so it does not touch the devcontainer's build of the same directory.

FROM node:22-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


# ✨ Debian 13 is named, because its PostgreSQL client is version 17, the server's own.
FROM python:3.13-slim-trixie AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN useradd --system --uid 10001 --no-create-home anville

# ✨ pg_dump and sftp, for the nightly backup, which runs in this same image (docs/server-approach.md, section 7).
# They also give the operator psql and pg_restore in the pod. Debian's security updates set the versions.
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client openssh-client \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py gunicorn.conf.py ./
COPY config/ config/
COPY access/ access/
COPY engine/ engine/
COPY organisations/ organisations/
COPY pathways/ pathways/
COPY --from=frontend /build/frontend/dist/ frontend/dist/

# ✨ The settings will not load without these two, and collectstatic reads neither. They are set for this one
# command and are not kept in the image.
RUN DJANGO_SECRET_KEY=only-for-collectstatic DATABASE_URL=postgres://nowhere/nothing \
    python manage.py collectstatic --noinput

# ✨ Last, so that a new commit with unchanged code reuses every layer above.
ARG ANVILLE_COMMIT=unknown
ENV ANVILLE_COMMIT=${ANVILLE_COMMIT}
LABEL org.opencontainers.image.source="https://github.com/inconceivableza/anville" \
      org.opencontainers.image.revision="${ANVILLE_COMMIT}"

USER 10001
EXPOSE 8000
CMD ["gunicorn"]
