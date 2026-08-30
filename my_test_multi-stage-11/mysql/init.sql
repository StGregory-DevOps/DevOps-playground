CREATE TABLE IF NOT EXISTS bookmarks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(2048) NOT NULL,
    note VARCHAR(512),
    title VARCHAR(512),
    description TEXT,
    status ENUM('pending', 'processing', 'done', 'error') NOT NULL DEFAULT 'pending',
    error_message VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
