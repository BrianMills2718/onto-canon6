# Multi-Agent Coordination Protocol

onto-canon6 is worked on by multiple agent brains (Claude Code, Codex CLI,
OpenClaw). This document defines how they coordinate to avoid conflicts.

## The Problem

Codex uses git worktrees for isolated work. When it merges a worktree back
to main, it can overwrite commits made by another agent since the worktree
branched. This has happened: Codex merges overwrote main in at least one
session.

## Rules

### Before Starting Work

1. **Check active claims**: `ls ~/.claude/coordination/claims/` — if another
   agent has claimed overlapping scope, coordinate before editing.
2. **Check KNOWLEDGE.md `## Active Decisions`**: review any open decisions
   that might affect your work.
3. **Pull before editing**: `git pull --rebase` to start from current main.

### During Work

4. **Claim your scope**: For multi-file changes, write a claim file:
   ```bash
   echo "claude-code: editing config.py, config.yaml — 2026-04-02 20:00" \
     > ~/.claude/coordination/claims/onto-canon6-config.txt
   ```
5. **Commit frequently**: Every verified increment gets its own commit.
   Uncommitted work is invisible to other agents.

### Before Merging a Worktree

6. **Rebase, don't merge blind**: Inside the worktree:
   ```bash
   git fetch origin
   git rebase origin/main
   # resolve any conflicts
   git checkout main
   git merge --ff-only <worktree-branch>
   git push
   ```
7. **Never force-push main**: If the push fails, rebase and retry.
   Never `--force`.

### After Finishing

8. **Remove your claim file** so other agents know the scope is free.
9. **Update KNOWLEDGE.md** with any findings that would affect future agents.

## Authority

This protocol is enforced by convention, not tooling. All agent brains
(Claude Code, Codex, OpenClaw) are expected to follow it. Violations that
cause data loss should be documented in KNOWLEDGE.md so the pattern is
recorded.

## See Also

- `KNOWLEDGE.md` — cross-agent operational findings
- `~/.claude/coordination/` — claim files (not tracked by git)
- `~/projects/.claude/CLAUDE.md` — ecosystem-wide multi-agent rules
