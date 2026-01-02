-- Debug Script: Check Email Verification Status
-- Run this to see if verification is working properly

-- 1. Check all users and their verification status
SELECT 
    id,
    email,
    username,
    is_verified,
    created_at
FROM users
ORDER BY id DESC
LIMIT 10;

-- 2. Check pending email verifications
SELECT 
    ev.id,
    ev.user_id,
    u.email,
    u.username,
    ev.token,
    ev.expires_at,
    CASE 
        WHEN ev.expires_at > NOW() THEN 'Valid'
        ELSE 'Expired'
    END as status
FROM email_verifications ev
JOIN users u ON ev.user_id = u.id
ORDER BY ev.created_at DESC;

-- 3. Find users who clicked verification but still showing unverified
-- (These should NOT exist - if they do, there's a bug)
SELECT 
    id,
    email,
    username,
    is_verified,
    created_at
FROM users
WHERE is_verified = 0
AND id NOT IN (SELECT user_id FROM email_verifications WHERE expires_at > NOW());

-- 4. Manually verify a user if needed (REPLACE 1 with actual user_id)
-- UPDATE users SET is_verified = TRUE WHERE id = 1;

-- 5. Check data types of is_verified column
DESCRIBE users;
