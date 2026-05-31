# =============================================================================
# Dockerfile Multi-Stage — Frontend Hobbys (Vite + React + Nginx)
# =============================================================================
# Stage 1: Compila la SPA con Node.js
# Stage 2: Sirve los estáticos con Nginx y proxifica /api → backend FastAPI
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1 — BUILD
# Imagen base ligera de Node 20 (Debian slim) para compilar la SPA con Vite
# -----------------------------------------------------------------------------
FROM node:20-slim AS build

# Directorio de trabajo dentro del contenedor de build
WORKDIR /app

# Copiar solo manifiestos de dependencias primero → maximiza caché de Docker
# Si package.json no cambia, npm ci no se vuelve a ejecutar en builds posteriores
COPY package.json package-lock.json ./

# Instalación reproducible y más rápida que npm install (usa package-lock.json)
RUN npm ci

# Copiar el resto del código fuente de la aplicación
COPY . .

# ---------------------------------------------------------------------------
# Variables de entorno de build (Vite las inyecta en tiempo de compilación)
# ---------------------------------------------------------------------------
# URL base del API. Por defecto "/api" (ruta relativa); Nginx proxifica al backend.
# Sobrescribir en docker-compose con: build.args.VITE_API_BASE_URL
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Modo producción para optimizaciones de Vite/Rollup
ENV NODE_ENV=production

# Compilar la SPA → genera /app/dist con HTML, JS, CSS y assets estáticos
RUN npm run build

# -----------------------------------------------------------------------------
# STAGE 2 — PRODUCTION
# Nginx Alpine: imagen mínima (~40 MB) ideal para servir estáticos en producción
# -----------------------------------------------------------------------------
FROM nginx:1.27-alpine AS production

# Etiquetas OCI recomendadas para trazabilidad en registros de contenedores
LABEL org.opencontainers.image.title="hobbys-frontend" \
      org.opencontainers.image.description="SPA React (Vite) servida por Nginx con reverse proxy /api" \
      org.opencontainers.image.source="https://github.com/your-org/hobbys-frontend"

# Eliminar configuración por defecto de Nginx para evitar conflictos de server block
RUN rm -f /etc/nginx/conf.d/default.conf

# Copiar configuración personalizada: SPA routing, gzip, seguridad y proxy /api
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar únicamente los artefactos compilados desde el stage de build
COPY --from=build /app/dist /usr/share/nginx/html

# Puerto HTTP estándar expuesto por Nginx dentro del contenedor
EXPOSE 80

# Healthcheck: verifica que Nginx responda en localhost (útil en Docker Compose/K8s)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:80/ > /dev/null 2>&1 || exit 1

# Ejecutar Nginx en primer plano (requerido para que Docker mantenga el contenedor vivo)
CMD ["nginx", "-g", "daemon off;"]
