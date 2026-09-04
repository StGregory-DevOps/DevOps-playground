import { Router } from 'express';
import { pool } from '../db.js';
import { upload } from '../upload.js';

export const imagesRouter = Router();

// POST /api/images — загрузить изображение, создать задачу в очереди
imagesRouter.post('/', upload.single('image'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'Поле image обязательно' });
  }

  try {
    const result = await pool.query(
      `INSERT INTO images (original_filename, stored_filename, status)
       VALUES ($1, $2, 'pending')
       RETURNING id, original_filename, status, created_at`,
      [req.file.originalname, req.file.filename]
    );

    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Ошибка при сохранении в БД:', err);
    res.status(500).json({ error: 'Внутренняя ошибка сервера' });
  }
});

// GET /api/images — список всех изображений
imagesRouter.get('/', async (_req, res) => {
  const result = await pool.query(
    `SELECT id, original_filename, stored_filename, status,
            thumbnail_filename, grayscale_filename, error_message, created_at
     FROM images
     ORDER BY created_at DESC`
  );
  res.json(result.rows);
});

// GET /api/images/:id — статус одного изображения
imagesRouter.get('/:id', async (req, res) => {
  const result = await pool.query(
    `SELECT * FROM images WHERE id = $1`,
    [req.params.id]
  );

  if (result.rows.length === 0) {
    return res.status(404).json({ error: 'Не найдено' });
  }

  res.json(result.rows[0]);
});
