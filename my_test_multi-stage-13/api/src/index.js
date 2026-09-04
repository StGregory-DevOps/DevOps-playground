import express from 'express';
import { imagesRouter } from './routes/images.js';

const PORT = process.env.PORT || 3000;
const app = express();

app.get('/health', (_req, res) => res.json({ status: 'ok' }));
app.use('/images', imagesRouter);

app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(400).json({ error: err.message || 'Ошибка запроса' });
});

app.listen(PORT, () => {
  console.log(`API запущен на порту ${PORT}`);
});
