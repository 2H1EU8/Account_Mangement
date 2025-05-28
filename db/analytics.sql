-- Analytics tables
CREATE TABLE password_analytics (
    analytics_id SERIAL PRIMARY KEY,
    owner_username VARCHAR(50) NOT NULL,
    total_accounts INTEGER,
    avg_strength DECIMAL(5,2),
    weak_passwords INTEGER,
    medium_passwords INTEGER,
    strong_passwords INTEGER,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2FA tables  
CREATE TABLE totp_settings (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id),
    secret_key TEXT NOT NULL,
    backup_codes TEXT[], -- Store encrypted backup codes
    enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Password generation preferences
CREATE TABLE password_preferences (
    pref_id SERIAL PRIMARY KEY,
    owner_username VARCHAR(50) NOT NULL,
    min_length INTEGER DEFAULT 12,
    use_uppercase BOOLEAN DEFAULT true,
    use_lowercase BOOLEAN DEFAULT true,
    use_numbers BOOLEAN DEFAULT true,
    use_symbols BOOLEAN DEFAULT true,
    avoid_similar BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
