const { pool } = require('../config/db');
const { redisClient } = require('../config/redis');

const CACHE_TTL = 60; // секунд

async function getAllPosts(req, res, next) {
  try {
    const cacheKey = 'posts:all';
    const cached = await redisClient.get(cacheKey);
    if (cached) {
      return res.json({ source: 'cache', data: JSON.parse(cached) });
    }

    const result = await pool.query(
      'SELECT id, title, content, category, created_at FROM posts ORDER BY created_at DESC'
    );

    await redisClient.set(cacheKey, JSON.stringify(result.rows), { EX: CACHE_TTL });

    res.json({ source: 'db', data: result.rows });
  } catch (err) {
    next(err);
  }
}

async function getPostById(req, res, next) {
  try {
    const { id } = req.params;
    const cacheKey = `posts:${id}`;
    const cached = await redisClient.get(cacheKey);
    if (cached) {
      return res.json({ source: 'cache', data: JSON.parse(cached) });
    }

    const result = await pool.query('SELECT * FROM posts WHERE id = $1', [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }

    await redisClient.set(cacheKey, JSON.stringify(result.rows[0]), { EX: CACHE_TTL });

    res.json({ source: 'db', data: result.rows[0] });
  } catch (err) {
    next(err);
  }
}

async function createPost(req, res, next) {
  try {
    const { title, content, category } = req.body;

    if (!title || !content) {
      return res.status(400).json({ error: 'title and content are required' });
    }

    const result = await pool.query(
      'INSERT INTO posts (title, content, category) VALUES ($1, $2, $3) RETURNING *',
      [title, content, category || 'general']
    );

    await invalidateListCache();

    res.status(201).json({ data: result.rows[0] });
  } catch (err) {
    next(err);
  }
}

async function updatePost(req, res, next) {
  try {
    const { id } = req.params;
    const { title, content, category } = req.body;

    const result = await pool.query(
      `UPDATE posts SET
        title = COALESCE($1, title),
        content = COALESCE($2, content),
        category = COALESCE($3, category),
        updated_at = NOW()
       WHERE id = $4 RETURNING *`,
      [title, content, category, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }

    await invalidateListCache();
    await redisClient.del(`posts:${id}`);

    res.json({ data: result.rows[0] });
  } catch (err) {
    next(err);
  }
}

async function deletePost(req, res, next) {
  try {
    const { id } = req.params;

    const result = await pool.query('DELETE FROM posts WHERE id = $1 RETURNING id', [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Post not found' });
    }

    await invalidateListCache();
    await redisClient.del(`posts:${id}`);

    res.status(204).send();
  } catch (err) {
    next(err);
  }
}

async function invalidateListCache() {
  await redisClient.del('posts:all');
}

module.exports = {
  getAllPosts,
  getPostById,
  createPost,
  updatePost,
  deletePost,
};
