CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO posts (title, content, category) VALUES
    ('Первый пост', 'Это тестовое содержимое первого поста', 'news'),
    ('Docker для начинающих', 'Контейнеризация меняет подход к разработке', 'tech')
ON CONFLICT DO NOTHING;
