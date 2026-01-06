# Project Context & Architecture

## 1. Project Overview
**Name:** EduStory Platform  
**Goal:** Create an interactive educational storytelling platform with AI-generated content and PWA capabilities.  
**Tech Stack:**  
- Frontend: React 18.2 + Vite, PWA  
- Backend: Python 3.11 + FastAPI  
- Database: SQLite (dev), MySQL (prod)  
- Tools: Docker, Git, SQLAlchemy  

## 2. Architecture & Patterns  
*Rules the PLAN model must enforce:*  
- **Style:** Functional components with hooks, service-oriented architecture  
- **Structure:**  
  - Frontend: Feature-based components (src/components/)  
  - Backend: Modular routers (backend/routers/) and services (backend/services/)  
- **Naming:**  
  - PascalCase for React components  
  - snake_case for Python modules  
  - camelCase for JavaScript functions  
- **State Management:** Context API for global state, local state for components  

## 3. Active Context (Mutable)  
- Implementing offline capabilities for story playback  
- Developing voice customization features (TTS integration)  
- Optimizing MySQL query performance for story metadata  

## 4. Known Constraints  
- Must support Chrome, Firefox, Safari (latest 2 versions)  
- Audio files: MP3 format @ 128kbps max  
- MySQL 8.0+ required for production
