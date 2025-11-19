# Worktree Sync Workflow Instructions

<critical>The workflow execution engine is governed by: {project_root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {installed_path}/workflow.yaml</critical>
<critical>Communicate all responses in {communication_language}</critical>

<workflow>

<step n="1" goal="Determine which worktrees to sync" tag="input">

<check if="{{worktree_name}} is provided">
  <action>Set sync_target = single worktree</action>
  <action>Validate worktree_name exists in git worktree list</action>
  <check if="worktree not found">
    <output>❌ Error: Worktree '{{worktree_name}}' not found.

Available worktrees:
{{list_of_worktrees}}

Use `/worktree:status` to see all worktrees.</output>
    <action>HALT</action>
  </check>
</check>

<check if="{{sync_all}} is true OR {{worktree_name}} is null">
  <action>Set sync_target = all worktrees</action>
  <action>Run: git worktree list --porcelain</action>
  <action>Parse and collect all feature worktrees (exclude main repo)</action>
  <check if="no feature worktrees found">
    <output>📋 No feature worktrees to sync.

Only the main repository exists. Create a worktree with:
```
/worktree:new
```
</output>
    <action>HALT</action>
  </check>
</check>

</step>

<step n="2" goal="Fetch latest changes from remote" tag="fetch">

<output>Fetching latest changes from remote...</output>

<action>Run: git fetch --all --prune</action>

<check if="fetch failed">
  <output>❌ Failed to fetch from remote: {{error_message}}

Ensure you have network connectivity and permissions to access the remote repository.</output>
  <action>HALT</action>
</check>

<output>✅ Remote changes fetched successfully</output>

</step>

<step n="3" goal="Sync worktrees" tag="sync-worktrees">

<loop through="worktrees_to_sync">

<output>
---
**Syncing: {{worktree_name}}**
Path: `{{worktree_path}}`
</output>

<action>Load worktree metadata from state file</action>
<action>Get base_branch for this worktree</action>

<substep n="3.1" goal="Check for uncommitted changes">
  <action>Run: cd {{worktree_path}} && git status --porcelain</action>

  <check if="uncommitted changes exist">
    <output>⚠️ Uncommitted changes detected</output>

    <check if="{auto_stash} == true">
      <output>Auto-stashing changes...</output>
      <action>Run: cd {{worktree_path}} && git stash push -m "Auto-stash before sync - {date}"</action>
      <variable>stashed = true</variable>
      <check if="stash failed">
        <output>❌ Failed to stash changes: {{error_message}}

Please manually commit or stash changes in {{worktree_path}} before syncing.
Skipping this worktree.</output>
        <action>Continue to next worktree</action>
      </check>
      <output>✅ Changes stashed successfully</output>
    </check>

    <check if="{auto_stash} == false">
      <ask>Uncommitted changes found. Choose action:
1. Stash and continue
2. Skip this worktree
3. Abort sync</ask>

      <branch if="user chooses stash">
        <action>Run: cd {{worktree_path}} && git stash push -m "Manual stash before sync - {date}"</action>
        <variable>stashed = true</variable>
      </branch>

      <branch if="user chooses skip">
        <output>Skipping {{worktree_name}}</output>
        <action>Continue to next worktree</action>
      </branch>

      <branch if="user chooses abort">
        <output>Sync aborted by user</output>
        <action>HALT</action>
      </branch>
    </check>
  </check>
</substep>

<substep n="3.2" goal="Rebase onto base branch">
  <output>Rebasing onto {{base_branch}}...</output>

  <action>Run: cd {{worktree_path}} && git rebase origin/{{base_branch}}</action>

  <check if="rebase succeeded">
    <output>✅ Rebase successful</output>
    <action>Update state file: Set last_sync = {{current_timestamp}}</action>
  </check>

  <check if="rebase conflicts">
    <output>⚠️ Merge conflicts detected during rebase!

**Conflicts in {{worktree_path}}:**

{{conflict_files}}

**To resolve:**
1. Navigate to worktree: `cd {{worktree_path}}`
2. Resolve conflicts in the listed files
3. Stage resolved files: `git add <file>`
4. Continue rebase: `git rebase --continue`

Or abort rebase: `git rebase --abort`

Sync paused for this worktree. Other worktrees will continue syncing.</output>

    <check if="{{stashed}} == true">
      <output>Note: Your changes were stashed before the rebase. After resolving conflicts, restore them with:
```
git stash pop
```
</output>
    </check>

    <action>Mark worktree sync as incomplete</action>
    <action>Continue to next worktree</action>
  </check>

  <check if="rebase failed (other error)">
    <output>❌ Rebase failed: {{error_message}}

Skipping this worktree. Please investigate manually:
```
cd {{worktree_path}}
git status
```
</output>
    <action>Continue to next worktree</action>
  </check>
</substep>

<substep n="3.3" goal="Restore stashed changes if any">
  <check if="{{stashed}} == true">
    <output>Restoring stashed changes...</output>
    <action>Run: cd {{worktree_path}} && git stash pop</action>

    <check if="stash pop succeeded">
      <output>✅ Stashed changes restored</output>
    </check>

    <check if="stash pop conflicts">
      <output>⚠️ Conflicts when restoring stashed changes!

Your stashed changes conflict with the rebased code. To resolve:
```
cd {{worktree_path}}
# Resolve conflicts
git add <resolved-files>
git stash drop  # Or keep stash with your changes
```
</output>
    </check>
  </check>
</substep>

<output>✅ {{worktree_name}} synced successfully</output>

</loop>

</step>

<step n="4" goal="Display sync summary" tag="output">

<output>
---

**🔄 Sync Complete, {user_name}!**

**Summary:**
- **Total worktrees:** {{total_count}}
- **Synced successfully:** {{success_count}}
- **Skipped (uncommitted changes):** {{skipped_count}}
- **Failed (conflicts/errors):** {{failed_count}}

{{#if success_count > 0}}
**Successfully Synced:**
{{#each synced_worktrees}}
- ✅ {{name}} - Up to date with {{base_branch}}
{{/each}}
{{/if}}

{{#if failed_count > 0}}
**Failed/Conflicts:**
{{#each failed_worktrees}}
- ❌ {{name}} - {{reason}}
{{/each}}

Please resolve conflicts manually in the affected worktrees.
{{/if}}

**Next Steps:**
- View worktree status: `/worktree:status`
- Continue development in your synced worktrees
- Remember to sync regularly (daily for long-running features)

**Tips:**
- Sync before starting work each day
- Commit frequently to avoid large conflicts
- Use `/worktree:status` to monitor sync health
</output>

</step>

</workflow>
