# Catalog App

Каталог товаров: Flask + PostgreSQL + Nginx, поднимается через Docker Compose.

## Структура
project/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── templates/
│       └── index.html
├── static/
│   ├── style.css
│   └── script.js
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── .gitignore
## Запуск

1. Скопировать .env.example в .env и подставить свои значения:
cp .env.example .env
2. Поднять проект:
docker-compose up --build
3. Открыть в браузере: http://localhost:8080

## Сервисы
- web — Flask-приложение (порт 5000, внутри сети)
- db — PostgreSQL 16 (данные хранятся в volume db_data)
- nginx — отдаёт статику и проксирует запросы к Flask (порт 8080 наружу)

## Проверка здоровья
curl http://localhost:8080/health

