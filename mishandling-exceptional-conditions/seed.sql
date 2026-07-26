DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS activities;
DROP TABLE IF EXISTS store_items;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    user_id INTEGER NOT NULL UNIQUE,
    points INTEGER NOT NULL DEFAULT 0,
    introduction TEXT,
    vip INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE activities (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    points INTEGER NOT NULL
);

CREATE TABLE store_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    cost INTEGER NOT NULL,
    is_secret INTEGER NOT NULL DEFAULT 0
);

INSERT INTO users (username, password, name, user_id, points, introduction, vip) VALUES
    ('ctfuser', 'ctfpassword', 'Albert', 7701, 0, NULL, 0),
    ('bob', 'password123', 'Bob McBuilder', 7702, 350, 'Im a builder!', 0),
    ('dd', 'quackquack', 'Donald Duck', 7703, 1200, 'Computer science student', 1);

INSERT INTO activities (id, title, points) VALUES
    (1, 'Trivia', 100),
    (2, 'Tug of War', 250),
    (3, 'Class Test', 500),
    (4, 'Special Exam', 750),
    (5, 'Purple Pride Open Day', 150);

INSERT INTO store_items (id, name, cost, is_secret) VALUES
    (1, 'Super Secret Item', 100000, 1),
    (2, 'Campus Coffee', 50, 0),
    (3, 'Elite University Hoodie', 1000, 0);
