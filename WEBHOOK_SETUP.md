# EduSmart Automated Deployment with aaPanel Webhook

This guide explains how to set up automatic deployment of EduSmart using aaPanel's webhook feature.

## Overview

Every time you push to the `main` branch on GitHub, the webhook will:
1. Pull the latest code from your repository
2. Build fresh Docker images
3. Start the application automatically
4. Log all operations to `deploy.log`

## Prerequisites

- aaPanel installed on your VPS
- Git installed on the server
- Docker and Docker Compose installed
- SSH access to your VPS
- GitHub repository push access

## Setup Steps

### Step 1: Upload Deploy Script to VPS

SSH into your VPS and navigate to your project directory:

```bash
cd /www/wwwroot/edusmart
```

Copy the `deploy.sh` script to your VPS. You have two options:

**Option A: Direct copy (if you have the file)**
```bash
# From your local machine
scp deploy.sh root@your-vps-ip:/www/wwwroot/edusmart/
```

**Option B: Create on VPS**
```bash
# Create the script file on VPS
cat > /www/wwwroot/edusmart/deploy.sh << 'EOF'
[Copy the entire deploy.sh content here]
EOF
```

### Step 2: Make Script Executable

```bash
chmod +x /www/wwwroot/edusmart/deploy.sh
```

### Step 3: Configure in aaPanel

1. **Log in to aaPanel** (typically on port 8888)
2. Navigate to **Webhook** (usually under Tools or Plugins menu)
3. Click **Add Webhook**
4. Fill in the following details:

   | Field | Value |
   |-------|-------|
   | **Name** | EduSmart Auto Deploy |
   | **Path** | `/edusmart-deploy` (or any path you prefer) |
   | **Script** | `/www/wwwroot/edusmart/deploy.sh` |
   | **Host** | `127.0.0.1` or your server IP |

5. **Important**: Save the webhook URL that aaPanel generates. It will look like:
   ```
   http://your-vps-ip:8888/webhook?secret=YOUR_SECRET_TOKEN
   ```

### Step 4: Configure GitHub Webhook

1. Go to your GitHub repository: https://github.com/ign3el/edusmart
2. Click **Settings** → **Webhooks**
3. Click **Add webhook**
4. Fill in the details:

   | Field | Value |
   |-------|-------|
   | **Payload URL** | `http://your-vps-ip:8888/webhook?secret=YOUR_SECRET_TOKEN` |
   | **Content type** | `application/json` |
   | **Which events?** | Select **Push events** (only when you push to main branch) |
   | **Active** | ✓ Check this box |

5. Scroll down and click **Add webhook**

### Step 5: Test the Webhook

Make a test commit and push to GitHub:

```bash
echo "# Webhook test" >> README.md
git add README.md
git commit -m "Test webhook deployment"
git push origin main
```

Check if the deployment was triggered:

1. In aaPanel, go to **Webhook** → **Logs** (if available)
2. On your VPS, check the deploy log:
   ```bash
   tail -f /www/wwwroot/edusmart/deploy.log
   ```

You should see entries like:
```
[2025-12-29 10:15:30] Starting EduSmart Deployment Process
[2025-12-29 10:15:31] Step 1/6: Verifying webhook...
[2025-12-29 10:15:31] Step 2/6: Pulling latest code from GitHub...
...
```

## Monitoring Deployments

### Real-time Log View

Watch deployment logs as they happen:

```bash
tail -f /www/wwwroot/edusmart/deploy.log
```

### View Recent Deployments

See the last 50 lines:

```bash
tail -50 /www/wwwroot/edusmart/deploy.log
```

### Search for Errors

Find all errors in deployment history:

```bash
grep "ERROR" /www/wwwroot/edusmart/deploy.log
```

### Check Container Status

After deployment, verify containers are running:

```bash
docker ps | grep edusmart
```

## Troubleshooting

### Webhook Not Triggering

1. **Check GitHub webhook delivery**:
   - Go to GitHub repo → Settings → Webhooks → Click the webhook
   - Scroll to "Recent Deliveries" and check the response
   - If red ✗, click to see the error message

2. **Check aaPanel webhook logs**:
   - In aaPanel, look for webhook execution logs
   - Verify the webhook path and script location are correct

3. **Test webhook manually**:
   ```bash
   /www/wwwroot/edusmart/deploy.sh
   ```
   Check `deploy.log` for errors

### Build Failures

1. Check the full build log:
   ```bash
   tail -100 /www/wwwroot/edusmart/deploy.log
   ```

2. Check Docker error details:
   ```bash
   docker compose logs backend
   docker compose logs frontend
   ```

3. Common issues:
   - **Insufficient disk space**: `df -h` to check
   - **Port already in use**: Check if 8000 or 3004 are busy
   - **Git permission denied**: Ensure SSH keys are set up correctly
   - **Docker build out of memory**: Increase VPS RAM or enable swap

### Script Permissions

If you see "Permission denied" error:

```bash
sudo chmod +x /www/wwwroot/edusmart/deploy.sh
sudo chown root:root /www/wwwroot/edusmart/deploy.sh
```

## Security Considerations

### 1. Webhook Secret (Optional)

For additional security, set a webhook secret:

1. Generate a secret:
   ```bash
   openssl rand -hex 32
   ```

2. Add to aaPanel webhook URL:
   ```
   http://your-vps-ip:8888/webhook?secret=YOUR_GENERATED_SECRET
   ```

3. Set the same secret in GitHub webhook

### 2. IP Whitelist (Recommended)

Restrict webhook calls to GitHub's IP ranges:

GitHub's webhook IPs: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-githubs-ip-addresses

In your aaPanel or firewall, whitelist GitHub's IPs.

### 3. SSH Key Setup

Ensure your VPS has SSH keys configured for GitHub:

```bash
# Check if SSH key exists
ls -la ~/.ssh/id_rsa

# If not, generate one
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Add public key to GitHub
cat ~/.ssh/id_rsa.pub
# Copy output and add to GitHub Settings → SSH and GPG keys
```

## Deployment Log Format

The deploy log includes timestamps and status for each step:

```
[2025-12-29 10:15:30] ==========================================
[2025-12-29 10:15:30] Starting EduSmart Deployment Process
[2025-12-29 10:15:30] ==========================================
[2025-12-29 10:15:30] Repo: https://github.com/ign3el/edusmart.git
[2025-12-29 10:15:30] Branch: main
[2025-12-29 10:15:30] Directory: /www/wwwroot/edusmart
[2025-12-29 10:15:31] Step 1/6: Verifying webhook...
[2025-12-29 10:15:31] SUCCESS: Webhook verification passed
[2025-12-29 10:15:31] Step 2/6: Pulling latest code from GitHub...
[2025-12-29 10:15:33] SUCCESS: Git fetch completed
[2025-12-29 10:15:33] Step 3/6: Resetting to latest remote main branch...
[2025-12-29 10:15:33] SUCCESS: Reset to commit: a1b2c3d
[2025-12-29 10:15:34] Step 4/6: Stopping existing Docker containers...
[2025-12-29 10:15:36] SUCCESS: Containers stopped
[2025-12-29 10:15:36] Step 5/6: Building fresh Docker images (no cache)...
[2025-12-29 10:17:45] SUCCESS: Docker images built successfully
[2025-12-29 10:17:46] Step 6/6: Starting EduSmart application...
[2025-12-29 10:17:50] SUCCESS: Application started successfully
[2025-12-29 10:17:50] ==========================================
[2025-12-29 10:17:50] SUCCESS: Deployment completed successfully!
[2025-12-29 10:17:50] ==========================================
```

## Automated Backup of Deploy Logs

To keep deploy logs from growing too large, create a weekly rotation:

```bash
# Add to crontab
crontab -e

# Add this line (runs every Sunday at 2 AM)
0 2 * * 0 cd /www/wwwroot/edusmart && cp deploy.log deploy.log.$(date +\%Y\%m\%d) && echo "" > deploy.log
```

## Rollback If Deployment Fails

If a deployment breaks your application:

```bash
# Reset to previous commit
cd /www/wwwroot/edusmart
git reset --hard HEAD~1

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Next Steps

1. ✅ Upload `deploy.sh` to your VPS
2. ✅ Configure webhook in aaPanel
3. ✅ Add webhook URL to GitHub
4. ✅ Test with a trial push
5. ✅ Monitor `deploy.log` for future deployments

Your EduSmart application is now fully automated! Every push to `main` will trigger an automatic rebuild and restart.

---

**Support**: Check logs with `tail -f /www/wwwroot/edusmart/deploy.log` for any issues.
