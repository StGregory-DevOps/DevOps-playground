require('dotenv').config();
const express = require('express');
const postsRouter = require('./routes/posts');
const errorHandler = require('./middleware/errorHandler');
const { pool } = require('./config/db');
const { redisClient } = require('./config/redis');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    await redisClient.ping();
    res.json({ status: 'ok' });
  } catch (err) {
    res.status(503).json({ status: 'error', message: err.message });
  }
});

app.use('/api/posts', postsRouter);

app.use(errorHandler);

async function start() {
  try {
    await redisClient.connect();
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  } catch (err) {
    console.error('Failed to start server:', err);
    process.exit(1);
  }
}

start();
