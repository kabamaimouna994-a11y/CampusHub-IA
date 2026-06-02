# ─── Build stage ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copier package.json et installer les dépendances
COPY package*.json ./
RUN npm ci --silent

# Copier le code source et builder
COPY . .
RUN npm run build

# ─── Runtime stage (Nginx) ────────────────────────────────────────────────────
FROM nginx:alpine

# Copier le build Vite
COPY --from=builder /app/dist /usr/share/nginx/html

# Config Nginx pour React Router (SPA)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
