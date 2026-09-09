# Two targets share one dependency layer:
#   --target dev   Vite dev server with HMR (local work, see docker-compose.override.yml)
#   --target prod  static build served by nginx (what the server runs)
#
# Production must not run `vite dev`: it ships unminified modules — react-dom alone
# is 820 KB as a single response — and the edge proxy in front of this deployment
# truncates anything over ~104 KiB, which left the site blank.

FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm install

# ---------------------------------------------------------------- development
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

# ------------------------------------------------------------------- build
FROM deps AS builder
# Baked into the bundle at build time — a static build has no runtime env.
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
COPY . .
RUN npm run build

# ---------------------------------------------------------------- production
FROM nginx:alpine AS prod
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5173
