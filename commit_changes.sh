#!/bin/bash
echo "Staging changes..."
git add backend/main.py backend/services/gemini_service.py .gitignore
echo "Committing changes..."
git commit -m "Fixed JSON parsing and UnboundLocalError"
echo "Pushing to main branch..."
git push origin main
