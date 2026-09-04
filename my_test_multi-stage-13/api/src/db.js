import pg from 'pg';

const { Pool } = pg;

// node-postgres сам подхватывает PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE
// из окружения — они приходят через env_file в docker-compose.yml
export const pool = new Pool();

export async function withRetry(fn, { retries = 10, delayMs = 1000 } = {}) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt === retries) throw err;
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
}
