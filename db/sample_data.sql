-- Add some sample accounts with varying password strengths
INSERT INTO accounts 
(category_id, account_name, username, encrypted_password, url, password_strength, owner_username)
VALUES 
(1, 'Facebook', 'user1', 'encrypted_pass', 'facebook.com', 85, 'dhieu03'),
(2, 'Gmail', 'user2', 'encrypted_pass', 'gmail.com', 45, 'dhieu03'),
(3, 'Dropbox', 'user3', 'encrypted_pass', 'dropbox.com', 95, 'dhieu03'),
(4, 'Bank', 'user4', 'encrypted_pass', 'bank.com', 30, 'dhieu03'),
(5, 'Twitter', 'user5', 'encrypted_pass', 'twitter.com', 65, 'dhieu03');

-- Add analytics history
INSERT INTO password_analytics 
(owner_username, total_accounts, avg_strength, weak_passwords, medium_passwords, strong_passwords)
VALUES 
('dhieu03', 5, 64.0, 1, 2, 2);
