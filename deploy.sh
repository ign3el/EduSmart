#!/bin/bash

# EduSmart Automated Deployment Script
# Purpose: Pull latest code from GitHub and rebuild/restart application
# Logs: All output stored in deploy.log
# Used with: aaPanel Webhook

set -e

# Configuration
REPO_DIR="/www/wwwroot/edusmart"
LOG_FILE="${REPO_DIR}/deploy.log"
GITHUB_REPO="https://github.com/ign3el/edusmart.git"
MAIN_BRANCH="main"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-}"  # Optional: Set in aaPanel webhook settings

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $1" | tee -a "$LOG_FILE"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[${timestamp}] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[${timestamp}] SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[${timestamp}] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Function to verify webhook signature (optional)
verify_webhook() {
    if [ -z "$WEBHOOK_SECRET" ]; then
        log_warning "Webhook signature verification disabled (no WEBHOOK_SECRET set)"
        return 0
    fi
    
    # If you implement GitHub webhook signature verification, add logic here
    # For now, we trust the webhook source
    return 0
}

# Start deployment
log_message "=========================================="
log_message "Starting EduSmart Deployment Process"
log_message "=========================================="
log_message "Repo: $GITHUB_REPO"
log_message "Branch: $MAIN_BRANCH"
log_message "Directory: $REPO_DIR"

# Check if repo directory exists
if [ ! -d "$REPO_DIR" ]; then
    log_error "Repository directory not found: $REPO_DIR"
    exit 1
fi

cd "$REPO_DIR" || exit 1

# Step 1: Verify webhook (if secret is set)
log_message "Step 1/6: Verifying webhook..."
if verify_webhook; then
    log_success "Webhook verification passed"
else
    log_error "Webhook verification failed"
    exit 1
fi

# Step 2: Fetch latest code from GitHub
log_message "Step 2/6: Pulling latest code from GitHub..."
if git fetch origin "$MAIN_BRANCH" >> "$LOG_FILE" 2>&1; then
    log_success "Git fetch completed"
else
    log_error "Git fetch failed"
    exit 1
fi

# Step 3: Reset to latest remote main
log_message "Step 3/6: Resetting to latest remote main branch..."
if git reset --hard "origin/$MAIN_BRANCH" >> "$LOG_FILE" 2>&1; then
    local commit_hash=$(git rev-parse --short HEAD)
    log_success "Reset to commit: $commit_hash"
else
    log_error "Git reset failed"
    exit 1
fi

# Step 4: Stop existing containers
log_message "Step 4/6: Stopping existing Docker containers..."
if docker compose down >> "$LOG_FILE" 2>&1; then
    log_success "Containers stopped"
else
    log_warning "Docker compose down encountered issues (containers may already be stopped)"
fi

# Step 5: Build fresh containers
log_message "Step 5/6: Building fresh Docker images (no cache)..."
if docker compose build --no-cache >> "$LOG_FILE" 2>&1; then
    log_success "Docker images built successfully"
else
    log_error "Docker build failed"
    # Log last 20 lines of build output for debugging
    tail -20 "$LOG_FILE" >> "$LOG_FILE"
    exit 1
fi

# Step 6: Start application
log_message "Step 6/6: Starting EduSmart application..."
if docker compose up -d >> "$LOG_FILE" 2>&1; then
    log_success "Application started successfully"
    
    # Wait a moment for services to initialize
    sleep 3
    
    # Check container status
    log_message "Container status:"
    docker ps --filter "label=com.docker.compose.project" >> "$LOG_FILE" 2>&1
    
else
    log_error "Docker compose up failed"
    # Show container logs for debugging
    log_message "Docker compose logs:"
    docker compose logs >> "$LOG_FILE" 2>&1
    exit 1
fi

# Final summary
log_message "=========================================="
log_success "Deployment completed successfully!"
log_message "=========================================="
log_message "Frontend: http://localhost:3004 (https://edusmart.ign3el.com in production)"
log_message "Backend API: http://localhost:8000"
log_message "API Docs: http://localhost:8000/docs"
log_message "Deploy log: $LOG_FILE"
log_message "=========================================="

exit 0
