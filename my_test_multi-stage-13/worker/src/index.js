import fs from 'node:fs';
import { processNext } from './processor.js';

const POLL_INTERVAL_MS = Number(process.env.POLL_INTERVAL_MS || 3000);
const HEARTBEAT_PATH = '/tmp/heartbeat';

let stopping = false;

function touchHeartbeat() {
  fs.writeFileSync(HEARTBEAT_PATH, String(Date.now()));
}

async function loop() {
  while (!stopping) {
    let hadJob = false;
    touchHeartbeat();

    try {
      hadJob = await processNext();
    } catch (err) {
      console.error('[worker] Ошибка в цикле обработки:', err.message);
    }

    if (!hadJob) {
      await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
    }
  }
}

console.log(`[worker] Старт. Опрос очереди каждые ${POLL_INTERVAL_MS}мс`);
loop();

process.on('SIGTERM', () => {
  console.log('[worker] Получен SIGTERM, завершаюсь после текущей задачи');
  stopping = true;
});
