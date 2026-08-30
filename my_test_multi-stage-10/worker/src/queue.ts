import { Job, Worker } from 'bullmq'
import { Redis } from 'ioredis'

import { config } from './config.js'

const connection = new Redis(config.redisUrl, {
  maxRetriesPerRequest: null,
})

async function processJob(job: Job) {
  console.log(`[worker] обработка задачи ${job.id} (${job.name})`)
  await new Promise((resolve) => setTimeout(resolve, 500))
  return { processedAt: new Date().toISOString() }
}

export function startWorker() {
  const worker = new Worker(config.queueName, processJob, {
    connection,
    concurrency: config.concurrency,
  })

  worker.on('completed', (job) => {
    console.log(`[worker] задача ${job.id} завершена`)
  })

  worker.on('failed', (job, err) => {
    console.error(`[worker] задача ${job?.id} провалена:`, err.message)
  })

  return worker
}
