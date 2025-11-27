-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0
);

-- Talks (charlas)
CREATE TABLE IF NOT EXISTS talks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    track TEXT,
    start_time TEXT,
    end_time TEXT,
    location TEXT
);

-- Exhibitors (expositores)
CREATE TABLE IF NOT EXISTS exhibitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    sector TEXT,
    stand TEXT
);

-- Agenda del usuario (charlas guardadas)
CREATE TABLE IF NOT EXISTS user_talks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    talk_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (talk_id) REFERENCES talks(id)
);

-- Expositores guardados por el usuario
CREATE TABLE IF NOT EXISTS user_exhibitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exhibitor_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (exhibitor_id) REFERENCES exhibitors(id)
);
