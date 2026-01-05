# Memory Synchronization Rules
You are responsible for maintaining project continuity across sessions through the memory-bank system.

## Memory Bank Protocol

### Before Each Task
1. **Check Active Context:** Read `memory-bank/activeContext.md` to understand current focus
2. **Update Progress:** Review `memory-bank/progress.md` and mark completed tasks
3. **Log Decisions:** Add significant choices to `memory-bank/decisionLog.md`

### After Each Task
1. **Update Active Context:** Reflect current focus and next steps
2. **Progress Tracking:** Move tasks from pending → in progress → completed
3. **Decision Documentation:** Capture reasoning for architectural and technical choices

### Memory Bank Structure
- **productContext.md:** Project vision, user goals, key features
- **activeContext.md:** Current focus, immediate tasks, technical stack
- **progress.md:** Completed, in-progress, and pending tasks
- **decisionLog.md:** Architectural decisions with rationale and impact

## Integration with Modes

### Architect Mode
- Always start by reading productContext.md
- Update decisionLog.md with architectural choices
- Ensure new features align with established patterns

### Code Mode
- Check activeContext.md for current technical stack
- Update progress.md with implementation status
- Document any "code smell" refactors in decisionLog.md

### Debug Mode
- Review decisionLog.md for recent changes that might cause issues
- Update progress.md with bug fixes and lessons learned
- Add context to activeContext.md about debugging focus

## Memory Persistence
- All modes must contribute to memory-bank
- Decisions should be traceable back to requirements
- Progress should be measurable and honest
- Context should enable seamless session transitions