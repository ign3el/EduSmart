# SYSTEM OVERRIDE: SHAMS AI GLOBAL PROTOCOLS

## 🛑 1. GLASS BOX VISIBILITY
*   **CHECKBOX ANCHOR:** No empty boxes `[ ]` allowed upon turn completion. All checklists must be marked `[✅]` or explicitly `[x]` / `[-]` if skipped/failed.
*   **OVERLAY ENFORCEMENT:** All Chat, Analysis, Plans, and Reports must be output as **TOP-LEVEL MARKDOWN** in the Main Chat Window.
    *   Forbidden: Hiding critical thinking or results inside "Tool Outputs" or "Thought" blocks.
    *   Forbidden: Using `notify_user` for general status updates (use it only for blocking reviews).

## 🛡️ 2. MANDATORY QA GATE
*   **NO SHORTCUTS:** The cycle `Expert -> Architect -> Coder -> QA` is MANDATORY for all code changes.
*   **VERIFICATION:** Agents must attempt to *execute* code (build/test) to verify fixes, not just inspect text.
*   **COMMITMENT:** Steps are only considered "DONE" when logged in `TASK_HISTORY.md` with a lock status.

## 🤖 3. AGENT DISCIPLINE
*   **SPEAK FIRST:** Output the `# 🛑 [PERSONA]` Header before calling any tool.
*   **NO STUTTERING:** Do not repeat the Header for every tool call in a sequence.
*   **NO WIDGETS:** Use plain Markdown/Text for plans and specs.
