# syntax=docker/dockerfile:1

# ✨ The one image every environment runs (docs/server-approach.md, section 3). It is public, so nothing may go
# into it that the repository does not already publish: .dockerignore admits only what is copied below.

FROM node:22-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.13-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN useradd --system --uid 10001 --no-create-home anville
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py gunicorn.conf.py ./
COPY config/ config/
COPY access/ access/
COPY engine/ engine/
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
