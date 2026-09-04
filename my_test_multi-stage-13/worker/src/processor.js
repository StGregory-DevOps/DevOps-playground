import path from 'node:path';
import fs from 'node:fs';
import sharp from 'sharp';
import { pool } from './db.js';

const UPLOAD_DIR = process.env.UPLOAD_DIR || '/data/uploads';
const PROCESSED_DIR = process.env.PROCESSED_DIR || '/data/processed';

fs.mkdirSync(PROCESSED_DIR, { recursive: true });

// Забирает одну pending-задачу и сразу помечает её processing,
// чтобы при нескольких воркерах никто не схватил ту же запись —
// SELECT ... FOR UPDATE SKIP LOCKED делает это атомарно
async function claimNextJob(client) {
  const result = await client.query(
    `SELECT id, stored_filename
     FROM images
     WHERE status = 'pending'
     ORDER BY created_at
     FOR UPDATE SKIP LOCKED
     LIMIT 1`
  );

  if (result.rows.length === 0) return null;

  const job = result.rows[0];

  await client.query(
    `UPDATE images SET status = 'processing' WHERE id = $1`,
    [job.id]
  );

  return job;
}

async function processImage(job) {
  const inputPath = path.join(UPLOAD_DIR, job.stored_filename);
  const ext = path.extname(job.stored_filename);
  const base = path.basename(job.stored_filename, ext);

  const thumbnailFilename = `${base}_thumb${ext}`;
  const grayscaleFilename = `${base}_gray${ext}`;

  await sharp(inputPath)
    .resize(200, 200, { fit: 'cover' })
    .toFile(path.join(PROCESSED_DIR, thumbnailFilename));

  await sharp(inputPath)
    .grayscale()
    .toFile(path.join(PROCESSED_DIR, grayscaleFilename));

  return { thumbnailFilename, grayscaleFilename };
}

export async function processNext() {
  const client = await pool.connect();

  try {
    await client.query('BEGIN');
    const job = await claimNextJob(client);

    if (!job) {
      await client.query('COMMIT');
      return false; // очередь пуста
    }

    await client.query('COMMIT');

    try {
      const { thumbnailFilename, grayscaleFilename } = await processImage(job);

      await pool.query(
        `UPDATE images
         SET status = 'done',
             thumbnail_filename = $1,
             grayscale_filename = $2,
             processed_at = now()
         WHERE id = $3`,
        [thumbnailFilename, grayscaleFilename, job.id]
      );

      console.log(`[worker] Обработано изображение #${job.id}`);
    } catch (err) {
      console.error(`[worker] Ошибка обработки #${job.id}:`, err.message);
      await pool.query(
        `UPDATE images SET status = 'failed', error_message = $1 WHERE id = $2`,
        [err.message, job.id]
      );
    }

    return true; // была задача, стоит сразу проверить следующую
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}
