# Email Configuration Fix Guide

## Issue 1: Gmail Overriding FROM Address

### Problem
You want emails to show as coming from `edusmart@ign3el.com`, but Gmail SMTP is showing your Gmail address instead.

### Why This Happens
Gmail's SMTP server **automatically replaces** the FROM address with the authenticated user's email address as a security measure to prevent spoofing.

### Solutions (Choose One)

#### ✅ Solution 1: Add Custom Email as Gmail Alias (Recommended if using Gmail)

1. **Go to Gmail Settings**
   - Open Gmail → Click gear icon → "See all settings"
   - Go to "Accounts and Import" tab

2. **Add Send Mail As**
   - Find "Send mail as" section
   - Click "Add another email address"
   
3. **Enter Your Custom Email**
   - Name: `EduSmart`
   - Email: `edusmart@ign3el.com`
   - Uncheck "Treat as an alias"
   - Click "Next Step"

4. **Verify Ownership**
   - Gmail will send a verification email to `edusmart@ign3el.com`
   - Click the verification link or enter the code
   - Once verified, Gmail will allow sending from this address

5. **Set as Default (Optional)**
   - In "Send mail as" section
   - Click "make default" next to your custom email

**Result:** Emails will now show `EduSmart <edusmart@ign3el.com>` as the sender! ✅

---

#### ✅ Solution 2: Use Your Domain's SMTP Server

If your domain (`ign3el.com`) has its own email server:

Update `.env`:
```bash
MAIL_SERVER=mail.ign3el.com        # Your domain's SMTP server
MAIL_PORT=587                       # Usually 587 or 465
MAIL_USERNAME=edusmart@ign3el.com   # Your domain email
MAIL_PASSWORD=your-domain-email-password
MAIL_FROM=EduSmart <edusmart@ign3el.com>
```

---

#### ✅ Solution 3: Use a Transactional Email Service

Better for production - these allow custom FROM addresses:

**Option A: SendGrid (Free 100 emails/day)**
```bash
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=your_api_key_here
MAIL_FROM=EduSmart <edusmart@ign3el.com>
```

**Option B: AWS SES (Cheap, reliable)**
- Requires AWS account
- $0.10 per 1000 emails
- Supports custom FROM addresses

**Option C: Mailgun (Free 5000 emails/month)**
```bash
# Similar to SendGrid
```

---

## Issue 2: Verification Link Using localhost

### Problem
Verification links point to `http://localhost:5173` instead of `https://edusmart.ign3el.com`

### Solution

Your `.env` already has `APP_URL=https://edusmart.ign3el.com` which is correct!

**Make sure:**
1. The backend Docker container has access to the `.env` file
2. The environment variable is loaded in the container

**Check if environment variable is loaded:**
```bash
# In your backend container
docker exec -it edusmart-backend env | grep APP_URL
```

Should show: `APP_URL=https://edusmart.ign3el.com`

**If not showing:**
- Make sure `.env` file is in `/www/wwwroot/edusmart/` directory
- Restart the backend container:
  ```bash
  cd /www/wwwroot/edusmart
  docker-compose down
  docker-compose up -d
  ```

**Verify it's working:**
- Check backend logs when it starts
- Should see: `Frontend URL: https://edusmart.ign3el.com`

---

## Testing After Fixes

### Test Email Configuration
```bash
# Restart backend
docker-compose restart backend

# Check logs for configuration
docker logs edusmart-backend | grep "Email Service Configuration"
```

Should see:
```
Email Service Configuration:
  Backend: smtp
  SMTP Host: smtp.gmail.com:587
  From Email: EduSmart <edusmart@ign3el.com>
  Frontend URL: https://edusmart.ign3el.com
  STARTTLS: True
```

### Test Signup Flow
1. Sign up with a new account
2. Check the verification email
3. FROM should show `EduSmart <edusmart@ign3el.com>` (if Gmail alias is set up)
4. Verification link should be: `https://edusmart.ign3el.com/verify-email?token=...`

---

## Quick Fix Summary

**For FROM address:**
- Add `edusmart@ign3el.com` as Gmail alias (Settings → Accounts → Send mail as)

**For verification URL:**
- Already fixed! Just restart backend container to reload environment variables

---

## Current .env Configuration (Correct)

```bash
# ✅ These are correct
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=EduSmart <edusmart@ign3el.com>
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
APP_URL=https://edusmart.ign3el.com

# ✅ Add this if not present
EMAIL_BACKEND=smtp
```

After restarting the backend, the verification URL issue should be fixed. For the FROM address, follow Solution 1 above to add the Gmail alias.
