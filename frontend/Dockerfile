# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install deps first (layer-cached if package.json unchanged)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --frozen-lockfile

# Copy source and build
COPY frontend/ ./
RUN npm run build


# ── Stage 2: serve with nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

LABEL org.opencontainers.image.title="synapse-trace-frontend" \
      org.opencontainers.image.description="Synapse Trace — React frontend served by nginx" \
      org.opencontainers.image.source="$CI_PROJECT_URL"

# Remove default nginx config and replace with our SPA config
RUN rm /etc/nginx/conf.d/default.conf
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/api/health 2>/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
