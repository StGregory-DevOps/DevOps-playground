import { startWorker } from './queue.js'

console.log('[worker] запуск фонового обработчика очередей...')

const worker = startWorker()

async function shutdown(signal: string) {
  console.log(`[worker] получен сигнал ${signal}, завершение работы...`)
  await worker.close()
  process.exit(0)
}

process.on('SIGTERM', () => shutdown('SIGTERM'))
process.on('SIGINT', () => shutdown('SIGINT'))
