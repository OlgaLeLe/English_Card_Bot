-- Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Общая таблица слов
CREATE TABLE words (
    id SERIAL PRIMARY KEY,
    ru TEXT NOT NULL,
    en TEXT NOT NULL,
    part_of_speech TEXT
);

-- Личные слова пользователей
CREATE TABLE user_words (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    ru TEXT NOT NULL,
    en TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
