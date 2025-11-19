# Worktree Status Workflow Instructions

<critical>The workflow execution engine is governed by: {project_root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {installed_path}/workflow.yaml</critical>
<critical>Communicate all responses in {communication_language}</critical>

<workflow>

<step n="1" goal="Get all worktrees from git" tag="git-list">

<action>Run: git worktree list --porcelain</action>
<action>Parse output to extract:
- worktree path
- HEAD commit
- branch name
</action>

<check if="no worktrees found except main">
  <output>📋 No worktrees currently active

You have only the main repository. To create a worktree:
```
/worktree:new
```
</output>
  <action>HALT</action>
</check>

<action>Filter out main repository worktree (keep only feature worktrees)</action>

</step>

<step n="2" goal="Load worktree state tracking" tag="state-load">

<action>Load {state_file}</action>
<action>Read worktrees section</action>
<action>Parse tracked worktree metadata</action>

</step>

<step n="3" goal="Check health of each worktree" tag="health-check">

<action>For each worktree found in step 1:</action>

<loop through="git_worktrees">
  <action>Extract worktree name from path (directory name)</action>

  <action>Check if tracked in state file</action>
  <variable>is_tracked = worktree exists in state file</variable>

  <action>Run: cd {{worktree_path}} && git status --porcelain</action>
  <action>Count uncommitted changes</action>
  <variable>uncommitted_changes = count of modified/added/deleted files</variable>

  <action>Run: cd {{worktree_path}} && git rev-list --count origin/{{base_branch}}..HEAD</action>
  <variable>commits_ahead = count of commits ahead of base</variable>

  <action>Run: cd {{worktree_path}} && git rev-list --count HEAD..origin/{{base_branch}}</action>
  <variable>commits_behind = count of commits behind base</variable>

  <action>Check if .venv directory exists</action>
  <variable>has_venv = .venv exists</variable>

  <action if="{{is_tracked}}">Calculate days since last sync from state file</action>
  <variable>days_since_sync = days between now and last_sync timestamp</variable>

  <action>Determine health status:
- 🟢 HEALTHY: No uncommitted changes, up to date with base, synced recently
- 🟡 NEEDS_SYNC: Behind base branch by >0 commits OR >2 days since last sync
- 🟠 DIVERGED: Ahead of base by >5 commits OR behind by >10 commits
- 🔴 DIRTY: Has uncommitted changes
- ⚪ UNKNOWN: Not tracked in state file
</action>

  <action>Store health report for this worktree</action>
</loop>

</step>

<step n="4" goal="Display worktree status summary" tag="output">

<output>**📊 Worktree Status Report - {project_name}**

Total worktrees: {{count_of_worktrees}}
</output>

<loop through="health_reports">
<output>
---
**{{worktree_name}}** {{health_icon}}

- **Path:** `{{worktree_path}}`
- **Branch:** {{branch_name}}
- **Base:** {{base_branch}}
- **Status:** {{health_status}}
- **Commits:** {{commits_ahead}} ahead, {{commits_behind}} behind base
- **Changes:** {{uncommitted_changes}} uncommitted
- **Environment:** {{#if has_venv}}✅ .venv present{{else}}❌ No .venv{{/if}}
{{#if is_tracked}}- **Created:** {{created_date}}
- **Last Sync:** {{last_sync_date}} ({{days_since_sync}} days ago)
{{#if story_key}}- **Story:** {{story_key}}{{/if}}
{{else}}- **Tracking:** ⚠️ Not tracked in state file
{{/if}}

{{#if health_status == "HEALTHY"}}✅ Worktree is healthy and up to date{{/if}}
{{#if health_status == "NEEDS_SYNC"}}⚠️ Recommend syncing: `/worktree:sync {{worktree_name}}`{{/if}}
{{#if health_status == "DIVERGED"}}⚠️ Significantly diverged from base. Consider rebasing or merging.{{/if}}
{{#if health_status == "DIRTY"}}⚠️ Has uncommitted changes. Commit or stash before syncing.{{/if}}
{{#if health_status == "UNKNOWN"}}⚠️ Not tracked. This worktree may have been created manually.{{/if}}
</output>
</loop>

<output>
---

**Quick Actions:**

- Create new worktree: `/worktree:new`
- Sync worktree: `/worktree:sync <name>`
- Sync all worktrees: `/worktree:sync --all`
- Clean up worktree: `/worktree:cleanup <name>`

**Health Legend:**
- 🟢 HEALTHY - Up to date, clean working directory
- 🟡 NEEDS_SYNC - Behind base branch or not synced recently
- 🟠 DIVERGED - Significantly ahead or behind base
- 🔴 DIRTY - Has uncommitted changes
- ⚪ UNKNOWN - Not tracked by worktree manager
</output>

</step>

<step n="5" goal="Detect stale worktrees" tag="stale-detection">

<action>Check for worktrees in state file that don't exist in git worktree list</action>

<check if="stale worktrees found">
  <output>
**⚠️ Stale Worktrees Detected:**

The following worktrees are tracked in state file but no longer exist:

{{#each stale_worktrees}}
- {{name}} ({{path}})
{{/each}}

Run `/worktree:cleanup --prune` to clean up stale tracking entries.
</output>
</check>

</step>

</workflow>
