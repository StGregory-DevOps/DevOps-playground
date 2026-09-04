FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY . .

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/src ./src
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./
RUN mkdir -p /data/uploads /data/processed && chown -R node:node /data
EXPOSE 3000
USER node
CMD ["node", "src/index.js"]