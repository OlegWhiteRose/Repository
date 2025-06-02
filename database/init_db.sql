-- Удаление существующих таблиц
DROP TABLE IF EXISTS Report, Employee, Transaction, Deposit, Document, Client CASCADE;

CREATE TABLE IF NOT EXISTS Client (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    phone VARCHAR UNIQUE NOT NULL CHECK (phone ~ '^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$')
);

CREATE TABLE IF NOT EXISTS Document (
    id SERIAL PRIMARY KEY,
    passport_number VARCHAR NOT NULL,
    birth_date TIMESTAMP NOT NULL,
    gender VARCHAR NOT NULL CHECK (gender IN ('Male', 'Female')),
    client_id INT NOT NULL REFERENCES Client(id) ON DELETE CASCADE,
    agreement_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    security_word VARCHAR NOT NULL,
    agreement_status VARCHAR NOT NULL CHECK (agreement_status IN ('active', 'inactive')) DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS Deposit (
    id SERIAL PRIMARY KEY,
    amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    close_date TIMESTAMP CHECK (close_date >= open_date),
    open_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    interest_rate NUMERIC(5,2) NOT NULL CHECK (interest_rate >= 0),
    status VARCHAR NOT NULL CHECK (status IN ('open', 'closed', 'closed early')) DEFAULT 'open',
    term INTERVAL NOT NULL DEFAULT '1 year',
    type VARCHAR NOT NULL CHECK (type IN ('Savings', 'Student', 'Student+', 'Premier', 'Future Care', 'Social', 'Social+')) DEFAULT 'Savings',
    client_id INT NOT NULL REFERENCES Client(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Transaction (
    id SERIAL PRIMARY KEY,
    deposit_id INT NOT NULL REFERENCES Deposit(id) ON DELETE CASCADE,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR NOT NULL CHECK (type IN ('addition', 'opening', 'closing', 'early closing'))
);

CREATE TABLE IF NOT EXISTS Employee (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    phone VARCHAR UNIQUE NOT NULL CHECK (phone ~ '^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$')
);

CREATE TABLE IF NOT EXISTS Report (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_id INT NOT NULL REFERENCES Transaction(id) ON DELETE CASCADE,
    employee_id INT NOT NULL REFERENCES Employee(id) ON DELETE CASCADE
);

-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user'
);

-- Вставка тестовых пользователей
INSERT INTO users (username, password_hash, role)
VALUES ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin')
ON CONFLICT (username) DO NOTHING;

INSERT INTO users (username, password_hash, role)
VALUES ('user', '04f8996da763b7a969b1028ee3007569eaf3a635486ddab211d512c85b9df8fb', 'user')
ON CONFLICT (username) DO NOTHING;

-- Вставка тестовых данных
INSERT INTO Client (first_name, last_name, phone) VALUES
('Иван', 'Обломов', '+7 (926) 234-23-23'),
('Олег', 'Иванков', '+7 (926) 234-23-43'),
('Виктор', 'Ломакин', '+7 (916) 123-42-34'),
('Аня', 'Сверестова', '+7 (916) 455-35-53'),
('Алексей', 'Булочкин', '+7 (927) 242-34-43'),
('Виктор', 'Тетерев', '+7 (123) 123-12-31'),
('Елисей', 'Игорев', '+7 (213) 213-12-45'),
('Анатолий', 'Простов', '+7 (213) 123-13-13'),
('Василий', 'Васильцов', '+7 (243) 242-42-34');

INSERT INTO Document (passport_number, birth_date, gender, client_id, agreement_date, security_word, agreement_status) VALUES
('3242 424324', '2005-09-10', 'Male', 1, '2024-05-02', 'Рубль', 'active'),
('1231 231231', '2000-03-08', 'Male', 2, '2024-05-02', 'Кот', 'active'),
('3331 123231', '1998-06-05', 'Male', 3, '2024-05-02', 'Веник', 'active'),
('2342 343242', '2006-10-10', 'Female', 4, '2024-05-02', 'Рука', 'active'),
('1312 313213', '2003-05-23', 'Male', 5, '2024-05-02', 'Кошка', 'active');

INSERT INTO Deposit (amount, close_date, open_date, interest_rate, status, term, type, client_id) VALUES
(0, '2024-11-01', '2024-10-01', 5, 'closed', '1 year', 'Savings', 1),
(2500, '2025-01-01', '2024-10-01', 7, 'open', '1 month', 'Social', 2),
(0, '2024-12-09', '2024-10-09', 15, 'closed', '2 months', 'Future Care', 3),
(10000, '2025-02-01', '2024-11-01', 6, 'open', '6 months', 'Premier', 6),
(5000, '2025-03-01', '2024-11-01', 4, 'open', '1 year', 'Student+', 7),
(15000, '2025-06-01', '2024-11-01', 8, 'open', '2 years', 'Savings', 8),
(12000, '2025-07-01', '2024-11-01', 7, 'open', '3 months', 'Social', 9),
(4555, '2025-01-08', '2024-10-08', 10, 'open', '3 months', 'Social+', 1);

INSERT INTO Transaction (deposit_id, amount, date, type) VALUES
(1, 1050, '2024-11-01', 'closing'),
(2, 9257, '2024-12-09', 'early closing'),
(3, 1000, '2024-10-31', 'opening'),
(4, 5000, '2024-12-20', 'closing'),
(1, 500, '2024-11-05', 'opening'),
(2, 1000, '2024-11-06', 'closing'),
(3, 2000, '2024-11-07', 'early closing'),
(4, 3000, '2024-11-08', 'addition'),
(1, 1500, '2024-11-09', 'closing'),
(2, 4500, '2024-11-10', 'opening'),
(3, 1000, '2024-11-11', 'addition'),
(4, 2000, '2024-11-12', 'early closing'),
(1, 1200, '2024-11-13', 'opening'),
(2, 3000, '2024-11-14', 'closing'),
(3, 500, '2024-11-15', 'early closing'),
(4, 7000, '2024-11-16', 'addition'),
(1, 3500, '2024-11-17', 'closing'),
(2, 6500, '2024-11-18', 'opening'),
(3, 1500, '2024-11-19', 'addition'),
(4, 10000, '2024-11-20', 'early closing'),
(1, 2000, '2024-11-21', 'closing'),
(2, 4000, '2024-11-22', 'opening'),
(3, 2500, '2024-11-23', 'addition'),
(5, 3000, '2024-11-02', 'opening'),  
(6, 2000, '2024-11-03', 'opening'),  
(7, 5000, '2024-11-04', 'addition'), 
(8, 7000, '2024-11-05', 'opening'),
(4, 5000, '2024-11-24', 'early closing');

INSERT INTO Employee (first_name, last_name, phone) VALUES
('Василий', 'Уткин', '+7 (916) 234-32-42'),
('Олег', 'Васьков', '+7 (916) 234-24-32'),
('Кирилл', 'Куприянов', '+7 (234) 234-32-43'),
('Кот', 'Котов', '+7 (123) 132-13-32');

INSERT INTO Report (content, transaction_id, employee_id) VALUES
('Отчет по закрытию вклада', 1, 1),
('Отчет по досрочному закрытию', 2, 2),
('Открытие нового вклада', 3, 3); 