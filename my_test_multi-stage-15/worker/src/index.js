import { createClient } from "redis";

import { checkUrl } from "./checker.js";

const REDIS_URL = process.env.REDIS_URL ?? "redis://localhost:6379/0";
const CHECK_TIMEOUT_MS = Number(process.env.CHECK_TIMEOUT_MS ?? 5000);
const JOB_TTL_SECONDS = Number(process.env.JOB_TTL_SECONDS ?? 3600);

const QUEUE_KEY = "linkwatch:queue";
const JOB_PREFIX = "linkwatch:job:";
const POLL_TIMEOUT_SECONDS = 5;

let running = true;

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    console.log(`Received ${signal}, stopping after the current job`);
    running = false;
  });
}

async function processJob(client, jobId) {
  const key = `${JOB_PREFIX}${jobId}`;
  const url = await client.hGet(key, "url");
  if (!url) {
    console.warn(`Job ${jobId} expired or missing, skipping`);
    return;
  }

  const outcome = await checkUrl(url, { timeoutMs: CHECK_TIMEOUT_MS });

  await client.hSet(key, {
    status: "done",
    result: outcome.result,
    http_status: String(outcome.httpStatus),
    response_ms: String(outcome.responseMs),
    error: outcome.error,
    checked_at: String(Math.floor(Date.now() / 1000)),
  });
  await client.expire(key, JOB_TTL_SECONDS);

  console.log(`Job ${jobId}: ${url} is ${outcome.result} (${outcome.responseMs} ms)`);
}

async function main() {
  const client = createClient({ url: REDIS_URL });
  client.on("error", (err) => console.error("Redis error:", err.message));
  await client.connect();
  console.log("Worker started");

  while (running) {
    const item = await client.brPop(QUEUE_KEY, POLL_TIMEOUT_SECONDS);
    if (item) {
      await processJob(client, item.element);
    }
  }

  await client.quit();
  console.log("Worker stopped");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
