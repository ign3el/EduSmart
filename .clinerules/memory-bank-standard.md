# MEMORY BANK RULE
- **Requirement**: Use the `/memory-bank` directory for persistent context.
- **Action**: Read `activeContext.md` and `progress.md` at the start of every session.
- **Maintenance**: Update the `progress.md` log after every successful code change.
- **Request Saving**: Use the memory bank to avoid "exploring" the codebase. If the file is marked as "completed" in `progress.md`, do not re-read it.

## Sonnet-Enhanced Storage Format
### Progress.md Structure
```markdown
## [Timestamp] Task: [Task Name]
- **Model Used**: Haiku (Free)
- **Complexity Score**: X.X/10
- **Files Modified**: N
- **Cost**: $0.XXX
- [x] Pattern analysis
- [x] Blueprint generation
- [ ] Implementation
- [ ] Memory Bank update
- [ ] Cost verification
```

### DecisionLog.md Structure
```markdown
## [Timestamp] Task: [Task Name]
- **Model Used**: Haiku/Sonnet
- **Complexity Score**: X.X/10
- **Files**: [file1, file2]
- **Reasoning**: 
  - Pattern match: [details]
  - Memory Bank: [reference]
  - Cost: $0.XXX
- **Alternative Considered**: [brief description]
```

### ActiveContext.md Enhancements
- Auto-calculate complexity score before execution
- Track model usage patterns
- Store cost estimates for future reference
- Log fallback triggers and reasons
