# =============================================================
# Dockerfile — Multi-stage build (buenas prácticas DevOps)
#
# Stage 1 (builder): instala dependencias en entorno aislado
# Stage 2 (runner):  imagen mínima, usuario non-root, solo
#                    artefactos necesarios — reduce superficie
#                    de ataque y tamaño de imagen.
# =============================================================

# ── Stage 1: builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Copiar solo el archivo de dependencias primero (aprovecha cache de capas)
COPY requirements.txt .

# Instalar dependencias en directorio local (sin instalar como root en el sistema)
RUN pip install --upgrade pip --no-cache-dir \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runner ──────────────────────────────────────────
FROM python:3.11-slim AS runner

# Metadatos de la imagen
LABEL maintainer="cesar-bar-d" \
      description="DevOps-Final: Automatización de red Cisco con RESTCONF" \
      version="1.0"

WORKDIR /app

# Copiar dependencias instaladas desde el builder
COPY --from=builder /install /usr/local

# Copiar el código fuente (no se copia .env — se monta en runtime)
COPY src/ ./src/
COPY tests/ ./tests/

# Crear directorio de reportes con permisos adecuados
RUN mkdir -p /app/reports

# Crear usuario no privilegiado con UID 900 (coincide con el usuario devasc
# de la DEVASC VM) para que el volumen reports/ sea escribible sin conflictos
RUN adduser --disabled-password --gecos "" --uid 900 appuser 2>/dev/null || true \
 && chown -R appuser:appuser /app

USER appuser

# Variable de entorno para que Python no genere .pyc y muestre logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.main"]
