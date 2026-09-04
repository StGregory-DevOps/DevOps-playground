CREATE TABLE IF NOT EXISTS images (
    id                  SERIAL PRIMARY KEY,
    original_filename   VARCHAR(255) NOT NULL,
    stored_filename     VARCHAR(255) NOT NULL,
    status              VARCHAR(20)  NOT NULL DEFAULT 'pending',
    thumbnail_filename  VARCHAR(255),
    grayscale_filename  VARCHAR(255),
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at        TIMESTAMPTZ
);

-- status: pending | processing | done | failed

CREATE INDEX IF NOT EXISTS idx_images_status ON images (status);
