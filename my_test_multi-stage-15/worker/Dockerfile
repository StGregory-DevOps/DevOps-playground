FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY src ./src

FROM node:20-alpine AS runtime
WORKDIR /app
COPY --from=builder --chown=node:node /app/ ./
USER node
CMD ["node", "src/index.js"]
