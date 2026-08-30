# Dockerfilr for worker

FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build


FROM node:20-alpine
WORKDIR /app

COPY --from=builder /app/package*.json ./
COPY --from=builder --chown=node:node /app/dist ./dist 
# Устанавливаем ТОЛЬКО продакшен-зависимости(без TypeScript и dev-пакетов)
RUN npm install --omit=dev

RUN chown -R node:node /app

USER node

CMD ["node", "dist/index.js"]