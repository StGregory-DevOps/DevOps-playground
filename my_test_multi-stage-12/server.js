'use strict';

const express = require('express');
const path = require('path');
const os = require('os');
const Redis = require('ioredis');

// ---------------------------------------------------------------------------
// Конфигурация из переменных окружения
// ---------------------------------------------------------------------------
const PORT = process.env.PORT || 3000;
const REDIS_HOST = process.env.REDIS_HOST || 'localhost';
const REDIS_PORT = process.env.REDIS_PORT || 6379;

const REQUEST_COUNT_KEY = 'infra:request_count';
const LOGS_KEY = 'infra:logs';
const SERVERS_KEY = 'infra:servers';
const LOGS_MAX_LENGTH = 50;
const SIMULATION_INTERVAL_MS = 4000;

// ---------------------------------------------------------------------------
// Простой JSON-логгер (удобно читать через `docker logs`)
// ---------------------------------------------------------------------------
function log(level, message, meta = {}) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...meta,
  };
  console.log(JSON.stringify(entry));
}

// ---------------------------------------------------------------------------
// Подключение к Redis
// ---------------------------------------------------------------------------
const redis = new Redis({
  host: REDIS_HOST,
  port: Number(REDIS_PORT),
  retryStrategy(times) {
    const delay = Math.min(times * 200, 3000);
    return delay;
  },
  maxRetriesPerRequest: 2,
  lazyConnect: false,
});

let redisConnected = false;

redis.on('connect', () => {
  log('info', 'redis_connected', { host: REDIS_HOST, port: REDIS_PORT });
});

redis.on('ready', () => {
  redisConnected = true;
});

redis.on('error', (err) => {
  redisConnected = false;
  log('error', 'redis_error', { error: err.message });
});

redis.on('close', () => {
  redisConnected = false;
  log('warn', 'redis_connection_closed');
});

// ---------------------------------------------------------------------------
// Express-приложение
// ---------------------------------------------------------------------------
const app = express();
app.disable('x-powered-by');
app.use(express.json());

// Логирование каждого входящего HTTP-запроса
app.use((req, res, next) => {
  const startedAt = Date.now();
  res.on('finish', () => {
    log('info', 'http_request', {
      method: req.method,
      path: req.originalUrl,
      status: res.statusCode,
      durationMs: Date.now() - startedAt,
      ip: req.ip,
    });
  });
  next();
});

// Счётчик запросов в Redis (не блокирует ответ при ошибке Redis)
app.use((req, res, next) => {
  if (redisConnected) {
    redis.incr(REQUEST_COUNT_KEY).catch((err) => {
      log('error', 'request_counter_failed', { error: err.message });
    });
  }
  next();
});

// Статика: public/index.html будет автоматически отдаваться на GET /
app.use(express.static(path.join(__dirname, 'public')));

// --- GET /health -------------------------------------------------------
app.get('/health', (req, res) => {
  const isHealthy = redisConnected;

  res.status(isHealthy ? 200 : 500).json({
    status: isHealthy ? 'OK' : 'ERROR',
    redis: redisConnected ? 'connected' : 'disconnected',
    uptime: process.uptime(),
  });
});

// --- GET /api/metrics ----------------------------------------------------
app.get('/api/metrics', async (req, res) => {
  try {
    let requestCountRaw = null;
    let logsRaw = [];
    let serversRaw = null;

    if (redisConnected) {
      [requestCountRaw, logsRaw, serversRaw] = await Promise.all([
        redis.get(REQUEST_COUNT_KEY),
        redis.lrange(LOGS_KEY, 0, LOGS_MAX_LENGTH - 1),
        redis.get(SERVERS_KEY),
      ]);
    }

    const requestCount = requestCountRaw ? parseInt(requestCountRaw, 10) : 0;

    const recentLogs = (logsRaw || [])
      .map((item) => {
        try {
          return JSON.parse(item);
        } catch {
          return null;
        }
      })
      .filter(Boolean);

    const servers = serversRaw ? JSON.parse(serversRaw) : getDefaultServers();

    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const memoryPercent = Math.round(((totalMem - freeMem) / totalMem) * 100);
    const cpuCount = os.cpus().length || 1;
    const loadAvg = os.loadavg()[0];
    const cpuPercent = Math.max(0, Math.min(100, Math.round((loadAvg / cpuCount) * 100)));

    res.json({
      timestamp: new Date().toISOString(),
      redis: redisConnected ? 'connected' : 'disconnected',
      requestCount,
      system: {
        hostname: os.hostname(),
        platform: os.platform(),
        cpuPercent,
        memoryPercent,
        uptimeSeconds: Math.round(process.uptime()),
      },
      servers,
      recentLogs,
    });
  } catch (err) {
    log('error', 'metrics_endpoint_failed', { error: err.message });
    res.status(500).json({ error: 'internal_error' });
  }
});

function getDefaultServers() {
  return [
    { name: 'web-01', status: 'online', cpu: 22, ram: 34 },
    { name: 'web-02', status: 'online', cpu: 19, ram: 31 },
    { name: 'db-primary', status: 'online', cpu: 41, ram: 57 },
    { name: 'cache-redis', status: 'online', cpu: 14, ram: 24 },
    { name: 'worker-01', status: 'online', cpu: 27, ram: 42 },
  ];
}

// ---------------------------------------------------------------------------
// Фоновая симуляция инфраструктуры: раз в SIMULATION_INTERVAL_MS
// обновляет статусы серверов и добавляет запись в лог событий (в Redis)
// ---------------------------------------------------------------------------
const SERVER_NAMES = ['web-01', 'web-02', 'db-primary', 'cache-redis', 'worker-01'];
const LOG_PATHS = ['/api/users', '/api/orders', '/api/metrics', '/health', '/api/auth/login', '/static/app.js'];
const LOG_METHODS = ['GET', 'POST', 'PUT', 'DELETE'];
const STATUS_POOL = [200, 200, 200, 200, 200, 200, 404, 500, 200, 404];

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function pickRandom(arr) {
  return arr[randomInt(0, arr.length - 1)];
}

function statusFromLoad(cpu, ram) {
  if (cpu > 85 || ram > 85) return 'critical';
  if (cpu > 65 || ram > 70) return 'warning';
  return 'online';
}

async function simulateInfrastructure() {
  if (!redisConnected) return;

  try {
    const servers = SERVER_NAMES.map((name) => {
      const cpu = randomInt(10, 95);
      const ram = randomInt(15, 90);
      return { name, status: statusFromLoad(cpu, ram), cpu, ram };
    });
    await redis.set(SERVERS_KEY, JSON.stringify(servers));

    const statusCode = pickRandom(STATUS_POOL);
    const messages = { 200: 'OK', 404: 'Not Found', 500: 'Internal Server Error' };
    const logEntry = {
      timestamp: new Date().toISOString(),
      method: pickRandom(LOG_METHODS),
      path: pickRandom(LOG_PATHS),
      status: statusCode,
      message: messages[statusCode] || 'OK',
    };

    await redis.lpush(LOGS_KEY, JSON.stringify(logEntry));
    await redis.ltrim(LOGS_KEY, 0, LOGS_MAX_LENGTH - 1);
  } catch (err) {
    log('error', 'simulation_cycle_failed', { error: err.message });
  }
}

const simulationTimer = setInterval(simulateInfrastructure, SIMULATION_INTERVAL_MS);

// ---------------------------------------------------------------------------
// Запуск сервера
// ---------------------------------------------------------------------------
const server = app.listen(PORT, () => {
  log('info', 'server_started', { port: PORT, redisHost: REDIS_HOST, redisPort: REDIS_PORT });
});

// ---------------------------------------------------------------------------
// Graceful shutdown: SIGINT / SIGTERM
// ---------------------------------------------------------------------------
function shutdown(signal) {
  log('info', 'shutdown_initiated', { signal });

  clearInterval(simulationTimer);

  server.close(() => {
    log('info', 'http_server_closed');
    redis
      .quit()
      .then(() => {
        log('info', 'redis_connection_closed_gracefully');
        process.exit(0);
      })
      .catch((err) => {
        log('error', 'redis_quit_failed', { error: err.message });
        process.exit(0);
      });
  });

  // Принудительное завершение, если graceful shutdown завис
  setTimeout(() => {
    log('error', 'forced_shutdown_timeout');
    process.exit(1);
  }, 10000).unref();
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
