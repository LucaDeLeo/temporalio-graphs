# Git Worktree Workflow for Parallel Development

**Worktree Manager Agent** enables parallel feature development with multiple isolated Claude Code agents using git worktrees.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Workflows](#workflows)
4. [BMM Integration](#bmm-integration)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Command Reference](#command-reference)

## Quick Start

### Load the Worktree Manager Agent

```
/bmad:worktree:agents:manager
```

The agent will greet you with a quick status overview and menu of available commands.

### Create Your First Worktree

Option 1: From a BMM story
```
*new → Select "From BMM story" → Choose story
```

Option 2: Custom feature
```
*new → Select "Custom feature" → Enter feature name
```

### Check Worktree Status

```
*status
```

Shows all active worktrees with health indicators:
- 🟢 HEALTHY - Up to date, clean
- 🟡 NEEDS_SYNC - Behind base or stale
- 🟠 DIVERGED - Significantly ahead/behind
- 🔴 DIRTY - Uncommitted changes

### Sync with Main

```
*sync
```

Choose to sync one worktree or all worktrees. Rebases onto latest main.

### Clean Up Completed Worktree

```
*cleanup → Select worktree
```

Safely removes worktree after verifying merge status.

## Core Concepts

### What are Git Worktrees?

Git worktrees allow you to have multiple working directories linked to a single git repository. Each worktree:

- Has its own working directory
- Can check out a different branch
- Shares the .git directory (commits, branches, config)
- Has isolated dependencies (.venv, node_modules)

### Directory Structure

```
/Users/luca/dev/bounty/              # Main repo (stays on main)
/Users/luca/dev/bounty-wt/           # Worktrees directory
  ├── story-5-3-path-output/         # Feature worktree 1
  ├── epic-6-signals/                # Feature worktree 2
  └── bugfix-validation/             # Bugfix worktree 3
```

### Shared vs Isolated

**Shared across all worktrees:**
- .git directory (commits, branches, tags)
- Git config
- Git hooks
- CLAUDE.md project instructions

**Isolated per worktree:**
- Working directory files
- .venv (Python virtual environments)
- node_modules (Node dependencies)
- Build artifacts
- Uncommitted changes

### Parallel Development Pattern

1. **Create** - Spin up isolated worktree for feature/story
2. **Develop** - Open in separate Claude Code window, work independently
3. **Sync** - Daily rebase from main to stay current
4. **Merge** - When complete, merge to main via PR or direct merge
5. **Cleanup** - Remove worktree and branch

## Workflows

### Workflow 1: Story-Driven Development

**Scenario:** Implementing a BMM user story with DEV agent

```
# In main repo - Load Worktree Manager
/bmad:worktree:agents:manager

# Create worktree linked to story
*new
→ Select: "From BMM story"
→ Choose: "5-3-path-output"
→ Confirm creation

# Worktree created at: /Users/luca/dev/bounty-wt/story-5-3-path-output
# Branch: feature/story-5-3-path-output

# Open new Claude Code window
cd /Users/luca/dev/bounty-wt/story-5-3-path-output
code .

# In new window - Load DEV agent
/bmad:bmm:agents:dev

# Implement story
*develop-story
→ Agent reads Story Context
→ Implements all tasks per acceptance criteria
→ Runs tests

# Sync with main (daily)
/bmad:worktree:agents:manager
*sync story-5-3-path-output

# When complete - merge to main
git push origin feature/story-5-3-path-output
# Create PR and merge

# Clean up
*cleanup story-5-3-path-output

# Update story status
/bmad:bmm:workflows:story-done
```

### Workflow 2: Multi-Epic Parallelization

**Scenario:** Working on Epic 5 and Epic 6 simultaneously

```
# Create worktree for Epic 5
*new
→ Custom feature: "epic-5-production-ready"
→ Confirm

# Create worktree for Epic 6
*new
→ Custom feature: "epic-6-signals"
→ Confirm

# Check status
*status
→ Shows both worktrees active

# Work on Epic 5
cd /Users/luca/dev/bounty-wt/epic-5-production-ready
code .
# Open Claude Code, implement stories 5-3, 5-4, 5-5

# Work on Epic 6 in parallel
cd /Users/luca/dev/bounty-wt/epic-6-signals
code .
# Open separate Claude Code, implement stories 6-1, 6-2

# Epic 5 completes first - merge to main
cd /Users/luca/dev/bounty-wt/epic-5-production-ready
git push origin feature/epic-5-production-ready
# Merge PR

# Cleanup Epic 5
*cleanup epic-5-production-ready

# Sync Epic 6 with newly merged Epic 5
*sync epic-6-signals
→ Rebases onto main (now includes Epic 5)
→ Resolve any conflicts

# Complete Epic 6
# Merge and cleanup
```

### Workflow 3: Experimental Feature

**Scenario:** Testing a risky refactoring without affecting main

```
# Create experimental worktree
*new
→ Custom feature: "refactor-analyzer-experimental"

# Experiment freely
cd /Users/luca/dev/bounty-wt/refactor-analyzer-experimental
# Make aggressive changes
# Test thoroughly

# Option A: Experiment succeeded
git push origin feature/refactor-analyzer-experimental
# Create PR, review, merge
*cleanup refactor-analyzer-experimental

# Option B: Experiment failed
*cleanup refactor-analyzer-experimental
→ Select: "Force cleanup"
→ No harm to main branch - clean slate
```

### Workflow 4: Daily Sync Routine

**Scenario:** Maintaining multiple long-running feature branches

```
# Morning routine - sync all worktrees
/bmad:worktree:agents:manager
*sync
→ Select: "Sync all worktrees"
→ All worktrees rebase onto latest main

# Check for issues
*status
→ View health of all worktrees
→ Address any conflicts or warnings

# Continue development
# Each worktree is now up to date with main
```

## BMM Integration

The Worktree Manager integrates seamlessly with the BMM (BMad Method) workflow system.

### Story-Linked Worktrees

When creating a worktree from a BMM story:

1. **Automatic naming** - Branch name generated from story ID and title
2. **Metadata tracking** - Story key stored in worktree state
3. **Status coordination** - Cleanup can trigger story-done workflow
4. **Context awareness** - DEV agent knows which story it's implementing

### Story Status Synchronization

```
# Create worktree for story 5-3
*new → Select story 5-3

# Story status in sprint-status.yaml: ready-for-dev
# Worktree created and linked

# After development and merge
*cleanup story-5-3

# Optional: Auto-trigger story-done
→ Updates sprint-status.yaml: ready-for-dev → done
```

### Multi-Agent Coordination

```
# PM Agent - Creates stories
/bmad:bmm:agents:pm
*create-story → Story 5-3 drafted

# SM Agent - Marks story ready
/bmad:bmm:agents:sm
*story-ready 5-3 → Status: ready-for-dev

# Worktree Manager - Creates worktree
/bmad:worktree:agents:manager
*new → Select story 5-3 → Worktree created

# DEV Agent - Implements story
cd /Users/luca/dev/bounty-wt/story-5-3
/bmad:bmm:agents:dev
*develop-story → Implements per Story Context

# Worktree Manager - Cleanup after merge
/bmad:worktree:agents:manager
*cleanup story-5-3

# SM Agent - Mark story done
/bmad:bmm:agents:sm
*story-done 5-3
```

## Best Practices

### 1. Keep Worktrees Short-Lived

**Good:** Hours to days
- Small features, single stories
- Bug fixes
- Quick experiments

**Avoid:** Weeks to months
- Risk of divergence
- Merge conflict accumulation
- Stale dependencies

### 2. Sync Daily

```
# Before starting work each day
*sync <worktree-name>
```

Benefits:
- Smaller, easier conflicts
- Stay aligned with team changes
- Fresher dependencies

### 3. Commit Frequently

Small, focused commits make syncing easier:

```
# Good: Small commits
git commit -m "Add path generator skeleton"
git commit -m "Implement path validation"
git commit -m "Add tests for path generation"

# Avoid: Large commits
git commit -m "Complete entire path generation feature"
```

### 4. Clean Up Promptly

After merging a feature:

```
# Immediately cleanup
*cleanup <worktree-name>
```

Benefits:
- Free disk space
- Avoid stale worktree accumulation
- Clear mental model of active work

### 5. Use Descriptive Names

```
# Good names
story-5-3-path-output
epic-6-signals
bugfix-unreachable-detection
refactor-analyzer-ast

# Avoid vague names
test
feature
new-stuff
```

### 6. One Branch Per Worktree

Git enforces this automatically - you can't check out the same branch in multiple worktrees. This is a feature, not a limitation!

### 7. Monitor Health Status

```
# Regular health checks
*status

# Address warnings promptly
🟡 NEEDS_SYNC → *sync <worktree>
🔴 DIRTY → Commit or stash changes
🟠 DIVERGED → Review and rebase
```

### 8. Coordinate with Team

If multiple developers use worktrees:

- Use unique branch names (include initials if needed)
- Communicate about shared branches
- Don't force-push to shared branches from worktrees

### 9. Environment Isolation

Each worktree should have its own environment:

```
# Python projects
cd <worktree>
uv venv
source .venv/bin/activate
uv sync

# Node projects
cd <worktree>
npm install
```

Worktree Manager handles this automatically when `auto_setup_env: true`.

### 10. Backup Before Force Cleanup

If forcing cleanup of unmerged work:

```
# Create backup branch first
git branch backup/feature-name

# Then force cleanup
*cleanup feature-name → Force → Confirm
```

## Troubleshooting

### Merge Conflicts During Sync

**Problem:** Conflicts when rebasing onto main

**Solution:**
```
cd <worktree-path>

# View conflicts
git status

# Resolve conflicts in files
# Edit conflicting files, choose correct version

# Stage resolved files
git add <resolved-files>

# Continue rebase
git rebase --continue

# Or abort if needed
git rebase --abort
```

**Prevention:**
- Sync more frequently (daily)
- Make smaller, focused commits
- Communicate with team about overlapping work

### Stale Worktrees

**Problem:** Worktree exists in file system but not in git

**Solution:**
```
*cleanup --prune
```

This removes tracking entries for deleted worktrees.

**Or manually:**
```
git worktree prune
```

### Disk Space Issues

**Problem:** Multiple worktrees consuming too much space

**Solution:**
1. Check status: `*status`
2. Identify completed/stale worktrees
3. Clean up: `*cleanup <worktree>`
4. Remove build artifacts in remaining worktrees

Each worktree includes:
- Full working directory (~MB to GB depending on project)
- .venv or node_modules (100s of MB)
- Build artifacts

### Can't Delete Worktree (In Use)

**Problem:** Git refuses to delete worktree

**Solution:**
```
# Close all editors/terminals in worktree
# Then retry
*cleanup <worktree>

# If still fails, force:
*cleanup <worktree> → Force cleanup
```

### Uncommitted Changes Blocking Sync

**Problem:** Can't sync due to uncommitted changes

**Solution:**

Option 1: Commit changes
```
cd <worktree>
git add .
git commit -m "WIP: <description>"
*sync <worktree>
```

Option 2: Stash changes (auto-handled by sync)
```
*sync <worktree>
→ Auto-stashes changes
→ Rebases
→ Auto-restores stash
```

Option 3: Discard changes
```
cd <worktree>
git reset --hard HEAD
*sync <worktree>
```

### Branch Already Exists

**Problem:** Creating worktree with existing branch name

**Solution:**
```
# Option 1: Use existing branch
*new → Enter name → "Use existing branch"

# Option 2: Choose different name
*new → Enter different name

# Option 3: Delete old branch first
git branch -d old-branch-name
*new → Enter name
```

### State File Out of Sync

**Problem:** Worktree state doesn't match reality

**Solution:**
```
# View actual worktrees
git worktree list

# View tracked worktrees
*status

# Prune stale entries
*cleanup --prune

# Manually edit if needed
# File: .bmad/worktree/worktree-state.yaml
```

### Can't Find Worktree Manager

**Problem:** Slash command not recognized

**Solution:**
```
# Check installation
ls .claude/commands/bmad/worktree/

# Reload Claude Code or restart session

# Manual load
/bmad:worktree:agents:manager
```

## Command Reference

### Agent Commands

Load the Worktree Manager agent:
```
/bmad:worktree:agents:manager
```

Once loaded, these commands are available:

#### *status
Display status of all worktrees with health checks

**Usage:**
```
*status
```

**Output:**
- List of all active worktrees
- Health indicators (🟢🟡🟠🔴)
- Commits ahead/behind base
- Uncommitted changes count
- Last sync time
- Linked story (if any)

**Use when:**
- Morning routine check
- After team merges
- Before starting new work
- Debugging worktree issues

---

#### *new
Create a new worktree

**Usage:**
```
*new
```

**Interactive prompts:**
1. From BMM story or custom feature?
2. Story/feature name
3. Branch name (auto-generated if blank)
4. Base branch (default: main)
5. Confirmation

**Creates:**
- New git worktree
- Feature branch
- Virtual environment (if auto_setup_env: true)
- State tracking entry

**Use when:**
- Starting new story/feature
- Need isolated workspace
- Want to experiment safely

---

#### *sync
Sync one or all worktrees with base branch

**Usage:**
```
*sync
```

**Interactive prompts:**
1. Which worktree? (or "all")
2. Confirm if uncommitted changes (auto-stash)

**Actions:**
- Fetches latest from remote
- Rebases worktree onto base branch
- Updates last_sync timestamp
- Handles stash/unstash automatically

**Use when:**
- Daily routine (before starting work)
- After team merges
- Before merging your feature
- Resolving divergence

---

#### *cleanup
Safely remove completed worktree

**Usage:**
```
*cleanup
```

**Interactive prompts:**
1. Select worktree
2. Verify no uncommitted changes
3. Check merge status
4. Confirm deletion
5. Delete branch? (default: yes)

**Safety checks:**
- Uncommitted changes warning
- Unmerged commits warning
- Force confirmation for risky operations

**Removes:**
- Worktree directory
- Feature branch (optional)
- State tracking entry

**Use when:**
- After merging feature
- Abandoning experiment
- Freeing disk space
- Cleaning stale worktrees

---

#### *quick-overview
Display concise worktree inventory

**Usage:**
```
*quick-overview
```

**Output:**
Table with: Worktree | Branch | Status | Last Sync | Story

**Use when:**
- Quick status check
- Don't need full health details
- Overview of parallel work

---

#### *best-practices
Show worktree workflow guide

**Usage:**
```
*best-practices
```

**Output:**
- Golden rules
- Common patterns
- Troubleshooting tips
- Integration examples

---

#### *help
Show numbered menu

**Usage:**
```
*help
```

---

#### *exit
Exit Worktree Manager

**Usage:**
```
*exit
```

### Direct Workflow Commands

You can also invoke workflows directly without loading the agent:

```
/bmad:worktree:workflows:new
/bmad:worktree:workflows:status
/bmad:worktree:workflows:sync
/bmad:worktree:workflows:cleanup
```

## Configuration

Worktree Manager configuration is stored in `.bmad/worktree/config.yaml`:

```yaml
# Worktree root directory (relative to project root)
worktree_root: '{project-root}/../{project-name}-wt'

# Default settings
default_base_branch: main
auto_setup_env: true
python_env_tool: uv
auto_sync_on_create: true

# State tracking
state_file: '{project-root}/.bmad/worktree/worktree-state.yaml'

# BMM Integration
sprint_artifacts: '{project-root}/docs/sprint-artifacts'
sprint_status: '{sprint_artifacts}/sprint-status.yaml'
```

### Customization

Edit `.bmad/worktree/config.yaml` to customize:

**worktree_root** - Where worktrees are created
- Default: `../bounty-wt` (sibling to main repo)
- Can use absolute path: `/Users/luca/worktrees/bounty`

**default_base_branch** - Branch to fork from
- Default: `main`
- Can use: `develop`, `master`, etc.

**auto_setup_env** - Automatically setup environments
- `true`: Run uv sync or npm install automatically
- `false`: Manual setup required

**python_env_tool** - Python environment tool
- `uv`: Use uv (recommended)
- `venv`: Use standard venv

**auto_sync_on_create** - Sync base branch on creation
- `true`: Fetch latest before creating worktree
- `false`: Use local base branch state

## Advanced Usage

### Scripting with Worktree Manager

Create custom scripts that leverage worktree workflows:

```bash
#!/bin/bash
# create-story-worktree.sh - Automated worktree creation for story

STORY_KEY=$1

# Create worktree via workflow
echo "/bmad:worktree:workflows:new" | claude-code

# Setup story context
cd ../bounty-wt/$STORY_KEY
echo "/bmad:bmm:workflows:story-context" | claude-code

# Open in editor
code .
```

### Bulk Operations

Sync all worktrees in one command:

```
*sync → Select "Sync all worktrees"
```

Cleanup multiple worktrees:

```
*status → Note completed worktrees
*cleanup <worktree-1>
*cleanup <worktree-2>
*cleanup <worktree-3>
```

### Integration with CI/CD

Worktrees work seamlessly with CI/CD pipelines:

```yaml
# .github/workflows/feature-branch.yml
name: Feature Branch CI

on:
  push:
    branches:
      - 'feature/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          uv sync
          pytest
```

Each worktree branch triggers its own CI run independently.

## FAQs

**Q: Can I use worktrees without Claude Code?**
A: Yes! Worktrees are a git feature. Worktree Manager just provides a convenient interface.

**Q: Do worktrees work with remote repositories?**
A: Yes. Push branches from worktrees like normal: `git push origin feature/branch-name`

**Q: Can I move a worktree to a different directory?**
A: No. Use `*cleanup` and `*new` instead. Git worktrees are tied to their path.

**Q: What happens to stashes in worktrees?**
A: Each worktree has its own stash! Stashes are local to the worktree.

**Q: Can I check out the same branch in multiple worktrees?**
A: No. Git prevents this to avoid conflicts. This is a safety feature.

**Q: Do worktrees affect git hooks?**
A: Hooks are shared across all worktrees (from main .git/hooks).

**Q: Can I use worktrees for hotfixes?**
A: Absolutely! Create worktree from production branch, fix, merge back.

**Q: How do I update main repo while in worktree?**
A: Worktrees and main repo are independent. Update main repo separately:
```
cd /Users/luca/dev/bounty  # Main repo
git pull origin main
```

Then sync worktrees:
```
*sync --all
```

**Q: Can multiple users share worktrees?**
A: No. Worktrees are local to your machine. Use branches for collaboration.

## Resources

- **Git Worktree Docs**: https://git-scm.com/docs/git-worktree
- **BMM Documentation**: `docs/sprint-artifacts/`
- **Worktree Manager Agent**: `/bmad:worktree:agents:manager`
- **Issue Tracker**: Report issues in project GitHub

## Version History

- **v1.0** - Initial release (2025-11-19)
  - Core workflows: new, status, sync, cleanup
  - BMM integration
  - Atlas agent (Worktree Manager)
  - Auto environment setup
  - Health monitoring

---

**Happy parallel developing! 🌳**
