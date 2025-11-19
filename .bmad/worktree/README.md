# Worktree Manager Module

This module provides git worktree management for parallel feature development with Claude Code agents.

## Structure

```
.bmad/worktree/
├── README.md                    # This file
├── config.yaml                  # Configuration
├── worktree-state.yaml          # State tracking
├── agents/
│   └── manager.md               # Atlas - Worktree Manager Agent
└── workflows/
    ├── new/
    │   ├── workflow.yaml        # Workflow config
    │   └── instructions.md      # Workflow logic
    ├── status/
    │   ├── workflow.yaml
    │   └── instructions.md
    ├── sync/
    │   ├── workflow.yaml
    │   └── instructions.md
    └── cleanup/
        ├── workflow.yaml
        └── instructions.md
```

## Slash Commands

Commands are registered in `.claude/commands/bmad/worktree/`:

- `/bmad:worktree:workflows:new` - Create new worktree
- `/bmad:worktree:workflows:status` - Show worktree status
- `/bmad:worktree:workflows:sync` - Sync worktree(s)
- `/bmad:worktree:workflows:cleanup` - Remove worktree
- `/bmad:worktree:agents:manager` - Load Atlas agent

## Quick Start

### Load Agent
```
/bmad:worktree:agents:manager
```

### Create Worktree
```
*new
```

### Check Status
```
*status
```

### Sync with Main
```
*sync
```

### Clean Up
```
*cleanup
```

## Configuration

Edit `config.yaml` to customize:

- **worktree_root**: Where worktrees are created
- **default_base_branch**: Branch to fork from (default: main)
- **auto_setup_env**: Auto-run uv sync or npm install
- **python_env_tool**: uv or venv
- **auto_sync_on_create**: Fetch latest before creating

## State Tracking

`worktree-state.yaml` tracks all managed worktrees:

```yaml
worktrees:
  feature-name:
    path: /path/to/worktree
    branch: feature/branch-name
    base_branch: main
    created: 2025-11-19T12:00:00Z
    last_sync: 2025-11-19T14:30:00Z
    env_setup: true
    status: active
    story_key: "5-3-path-output"  # Optional BMM link
```

## BMM Integration

Worktree Manager integrates with BMM workflow system:

- Create worktrees from stories
- Link worktree to story in tracking
- Coordinate with sprint-status.yaml
- Auto-trigger story-done on cleanup (optional)

## Documentation

See `docs/WORKTREE_WORKFLOW.md` for comprehensive guide:

- Workflows and patterns
- Best practices
- Troubleshooting
- Command reference
- FAQ

## Version

Version: 1.0
Created: 2025-11-19
