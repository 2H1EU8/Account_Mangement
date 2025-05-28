-- Core tables for account management
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    icon TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(category_id),
    account_name VARCHAR(100) NOT NULL,
    username VARCHAR(255) NOT NULL,
    encrypted_password TEXT NOT NULL,
    url VARCHAR(255),
    last_password_change TIMESTAMP,
    next_password_change TIMESTAMP,
    password_strength INTEGER CHECK (password_strength BETWEEN 0 AND 100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(user_id),
    owner_username VARCHAR(50) NOT NULL
);

CREATE TABLE password_history (
    history_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(account_id) ON DELETE CASCADE,
    encrypted_password TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE security_settings (
    setting_id SERIAL PRIMARY KEY,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE password_reminders (
    reminder_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(account_id) ON DELETE CASCADE,
    reminder_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_accounts_category ON accounts(category_id);
CREATE INDEX idx_password_history_account ON password_history(account_id);
CREATE INDEX idx_reminders_account ON password_reminders(account_id);
CREATE INDEX idx_accounts_owner ON accounts(owner_username);

-- Insert default categories
INSERT INTO categories (name, icon) VALUES 
('Social Media', '🌐'),
('Email', '✉️'),
('Cloud Storage', '☁️'),
('Health', '🏥'),
('Utilities', '🔧'),
('Work', '💼');