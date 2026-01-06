<ANALYSIS>
We are adding a new user authentication feature in the backend and updating the login UI in frontend. 
Edge cases considered: invalid credentials, password reset flow, and multi-browser sessions. 
Regression risks identified: existing login and registration workflows must continue to work, CSS layout should not break existing pages.
</ANALYSIS>

<FILES_TO_CHANGE>
backend/auth/routes.py
backend/auth/services.py
frontend/src/components/LoginForm.jsx
frontend/src/styles/login.css
frontend/src/components/ErrorMessage.jsx
PROJECT_CONTEXT.md
TASK_HISTORY.md
</FILES_TO_CHANGE>

<PLAN_STEPS>
1. [Update] backend/auth/routes.py: Add new POST route for password reset with validation.
2. [Update] backend/auth/services.py: Implement secure token generation for password reset and login verification.
3. [Update] frontend/src/components/LoginForm.jsx: Add password reset UI, connect to new backend endpoint.
4. [Update] frontend/src/styles/login.css: Style password reset form, ensure no existing layout breaks.
5. [Update] frontend/src/components/ErrorMessage.jsx: Display backend validation errors safely.
6. [Command] Run `pytest backend/tests` to ensure no regression in authentication flows.
7. [Command] Run `npm run test:frontend` to validate UI updates do not break existing components.
8. [Command] Run `npm run lint` and format frontend code to maintain cleaner code standards.
9. [Update] TASK_HISTORY.md: Append new feature entry, including files modified, steps executed, and test results.
10. [Update] PROJECT_CONTEXT.md: Document new feature, edge cases, regression checks, and active session context.
</PLAN_STEPS>

<MEMORY_UPDATE>
TASK_HISTORY.md: Add entry "User Authentication Update" with files changed, test results, and timestamps.
PROJECT_CONTEXT.md: Document feature description, edge cases, regression risks, and notes on session context.
</MEMORY_UPDATE>
