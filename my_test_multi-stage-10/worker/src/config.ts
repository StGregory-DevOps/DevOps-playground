import 'dotenv/config'

export const config = {
  redisUrl: process.env.REDIS_URL ?? 'redis://redis_cache:6379/0',
  queueName: process.env.QUEUE_NAME ?? 'default-queue',
  concurrency: Number(process.env.WORKER_CONCURRENCY ?? 5),
}
