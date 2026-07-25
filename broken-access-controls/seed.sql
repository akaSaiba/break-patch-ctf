-- Initial DB data for the Security Engineering Student Portal

PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    bio TEXT NOT NULL DEFAULT '',
    user_id INTEGER NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK(role IN ('student', 'staff')),
    uuid TEXT NOT NULL UNIQUE
);

INSERT INTO users (id, username, password, name, bio, user_id, role, uuid) VALUES
(1, 'ctfuser', 'ctfpassword', 'Bob McBuilder', 'First-year security engineering student.', 5501, 'student', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'),
(2, 'jsmith', 'password123', 'Jordan Smith', 'Coffee-powered debugger.', 5502, 'student', 'b2c3d4e5-f6a7-8901-bcde-f12345678901'),
(3, 'egoist', 'letmein', 'Bob McStriker', 'CTF enthusiast and note-taker.', 5503, 'student', 'c3d4e5f6-a7b8-9012-cdef-123456789012'),
(4, 'alee', 'qwerty', 'Avery Lee', 'Loves access-control labs.', 5504, 'student', 'd4e5f6a7-b8c9-0123-def0-234567890123'),
(5, 'admin', 'admin', 'Admin', 'System administrator account.', 9999, 'staff', 'e5f6a7b8-c9d0-1234-ef01-345678901234');

CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    assignment TEXT NOT NULL,
    score TEXT NOT NULL,
    grade TEXT NOT NULL,
    submitted TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

INSERT INTO results (id, user_id, assignment, score, grade, submitted) VALUES
(1, 5501, 'Lab 1', '92/100', 'A-', '2026-02-10'),
(2, 5501, 'Lab 2', '85/100', 'B', '2026-03-01'),
(3, 5501, 'Midterm Exam', '78/100', 'C+', '2026-03-15'),
(4, 5501, 'Lab 3', '95/100', 'A', '2026-04-02'),
(5, 5502, 'Lab 1', '88/100', 'B+', '2026-02-11'),
(6, 5502, 'Lab 2', 'FLAG{NO00_MY_R4SUL7S}', 'A-', '2026-03-02'),
(7, 5502, 'Midterm Exam', '84/100', 'B', '2026-03-15'),
(8, 5503, 'Lab 1', '97/100', 'A', '2026-02-09'),
(9, 5503, 'Lab 2', '93/100', 'A', '2026-03-01'),
(10, 5503, 'Midterm Exam', '89/100', 'B+', '2026-03-15'),
(11, 5503, 'Lab 3', '100/100', 'A+', '2026-04-03'),
(12, 5504, 'Lab 1', '76/100', 'C', '2026-02-12'),
(13, 5504, 'Midterm Exam', '81/100', 'B-', '2026-03-15');

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_uuid TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (user_uuid) REFERENCES users(uuid)
);

INSERT INTO notes (id, user_uuid, title, content) VALUES
(1, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Week 1 Notes', 'Watch Extended Security Lectures'),
(2, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Password tip', 'DO NOT USE THE SAME PASSWORD FOR EVERYTHING'),
(3, 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Private research', 'Found a data breach in Moodle. REPORT TO COURSE ADMINS ASAP !!'),
(4, 'c3d4e5f6-a7b8-9012-cdef-123456789012', 'Super top secret notes', 'FLAG{G0T_Y0UR_NOT3S}' || char(10) || 'Do not share this UUID with anyone.'),
(5, 'd4e5f6a7-b8c9-0123-def0-234567890123', 'New tutorial times', 'Monday tutorial time moved to Thursday 11:00am');

CREATE TABLE exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL
);

INSERT INTO exams (id, course, title, content) VALUES
(1, 'Security Engineering', 'Final Exam',
 'Q1. Explain horizontal vs vertical privilege escalation.' || char(10) ||
 'Q2. Give one real-world example of an IDOR.' || char(10) ||
 'Q3. FLAG{FR33_HD_F0R_Y0U}');

CREATE TABLE exam_solutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    solution TEXT NOT NULL,
    FOREIGN KEY (exam_id) REFERENCES exams(id)
);

INSERT INTO exam_solutions (id, exam_id, title, solution) VALUES
(1, 1, 'Final Exam Solutions',
 'A1. Horizontal = same privilege tier, different object; vertical = higher privilege tier.' || char(10) ||
 'A2. Changing /api/results/{user_id} to another student ID.' || char(10) ||
 'A3. FLAG{3VEN_M0RE_FR33_HD_F0R_Y0U}');

DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence (name, seq) VALUES
('users', 5),
('results', 13),
('notes', 5),
('exams', 1),
('exam_solutions', 1);

COMMIT;
