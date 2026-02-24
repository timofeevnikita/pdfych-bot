"""SQL-схема базы данных ПДФыч."""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id    INTEGER PRIMARY KEY,
    username   TEXT,
    first_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_premium INTEGER DEFAULT 0
);
"""

CREATE_CONVERSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    input_format  TEXT    NOT NULL,
    output_format TEXT    NOT NULL,
    file_size     INTEGER,
    success       INTEGER DEFAULT 1,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

CREATE_CONVERSIONS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_conversions_user_date
    ON conversions(user_id, created_at);
"""

ALL_MIGRATIONS = [
    CREATE_USERS_TABLE,
    CREATE_CONVERSIONS_TABLE,
    CREATE_CONVERSIONS_INDEX,
]
