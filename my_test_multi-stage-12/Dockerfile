FROM node:18 AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev
COPY . .

FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/server.js ./server.js
COPY --from=builder /app/public ./public
COPY package*.json ./

EXPOSE 3000

CMD ["node", "server.js"]
