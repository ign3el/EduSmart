# MEMORY BANK RULE
- **Requirement**: Use the `/memory-bank` directory for persistent context.
- **Action**: Read `activeContext.md` and `progress.md` at the start of every session.
- **Maintenance**: Update the `progress.md` log after every successful code change.
- **Request Saving**: Use the memory bank to avoid "exploring" the codebase. If the file is marked as "completed" in `progress.md`, do not re-read it.
