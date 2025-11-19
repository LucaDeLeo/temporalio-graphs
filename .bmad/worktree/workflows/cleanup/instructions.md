# Worktree Cleanup Workflow Instructions

<critical>The workflow execution engine is governed by: {project_root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {installed_path}/workflow.yaml</critical>
<critical>Communicate all responses in {communication_language}</critical>

<workflow>

<step n="1" goal="Determine cleanup mode" tag="input">

<check if="{{prune}} is true">
  <action>Set cleanup_mode = prune_stale</action>
  <action>GOTO step 6 (prune stale entries)</action>
</check>

<check if="{{worktree_name}} is null">
  <output>📋 Select worktree to cleanup

Available worktrees:</output>

  <action>Run: git worktree list --porcelain</action>
  <action>Parse and list all feature worktrees (exclude main repo)</action>

  <check if="no feature worktrees found">
    <output>No feature worktrees to cleanup.

To prune stale tracking entries:
```
/worktree:cleanup --prune
```
</output>
    <action>HALT</action>
  </check>

  <action>Display worktrees with status indicators:
- 🟢 Merged (safe to remove)
- 🟡 Not merged (verify before removing)
- 🔴 Uncommitted changes (cannot remove safely)
</action>

  <ask>Select worktree to cleanup (enter name or number):</ask>
  <action>Set {{worktree_name}} from user selection</action>
</check>

<action>Validate worktree_name exists</action>
<check if="worktree not found">
  <output>❌ Error: Worktree '{{worktree_name}}' not found.

Use `/worktree:status` to see all worktrees.</output>
  <action>HALT</action>
</check>

</step>

<step n="2" goal="Load worktree metadata" tag="metadata">

<action>Run: git worktree list --porcelain</action>
<action>Find worktree by name and extract:
- worktree_path
- branch_name
- HEAD commit
</action>

<action>Load state file</action>
<action>Get worktree metadata:
- base_branch
- created date
- story_key (if exists)
</action>

<output>**Worktree to cleanup:**

- **Name:** {{worktree_name}}
- **Path:** `{{worktree_path}}`
- **Branch:** {{branch_name}}
- **Base:** {{base_branch}}
{{#if story_key}}- **Story:** {{story_key}}{{/if}}
</output>

</step>

<step n="3" goal="Safety checks" tag="validation">

<substep n="3.1" goal="Check for uncommitted changes">
  <action>Run: cd {{worktree_path}} && git status --porcelain</action>

  <check if="uncommitted changes exist">
    <output>⚠️ **Warning: Uncommitted changes detected!**

Files with changes:
{{list_of_changed_files}}

**Options:**
1. Commit changes first
2. Stash changes (saved for recovery)
3. Discard changes (⚠️ permanent)
4. Abort cleanup

Choose option:</output>

    <branch if="user chooses commit">
      <output>Please commit your changes first, then run cleanup again.</output>
      <action>HALT</action>
    </branch>

    <branch if="user chooses stash">
      <action>Run: cd {{worktree_path}} && git stash push -m "Stashed before cleanup - {date}"</action>
      <output>✅ Changes stashed successfully

To recover later:
```
cd {{worktree_path}}
git stash pop
```

(Note: Worktree will be removed, but stash remains in git repo)
</output>
    </branch>

    <branch if="user chooses discard">
      <ask>⚠️ **CONFIRM DISCARD**: Type 'DISCARD' to permanently delete uncommitted changes:</ask>
      <check if="user input != 'DISCARD'">
        <output>Cleanup aborted. Uncommitted changes preserved.</output>
        <action>HALT</action>
      </check>
      <output>Proceeding with discard...</output>
    </branch>

    <branch if="user chooses abort">
      <output>Cleanup aborted.</output>
      <action>HALT</action>
    </branch>
  </check>
</substep>

<substep n="3.2" goal="Check merge status">
  <check if="{{force}} is false">
    <action>Run: git branch --merged {{base_branch}} | grep {{branch_name}}</action>

    <check if="branch is NOT merged">
      <output>⚠️ **Warning: Branch not merged to {{base_branch}}**

This branch contains commits that are not in {{base_branch}}:

{{unmerged_commits}}

**Options:**
1. Cancel cleanup (merge or push first)
2. Force cleanup (⚠️ commits will be lost)
3. Keep branch, remove worktree only

Choose option:</output>

      <branch if="user chooses cancel">
        <output>Cleanup cancelled. Please merge or push your branch first:

```
cd {{worktree_path}}
git push origin {{branch_name}}
# Then create PR or merge to {{base_branch}}
```
</output>
        <action>HALT</action>
      </branch>

      <branch if="user chooses force">
        <ask>⚠️ **CONFIRM FORCE CLEANUP**: Type 'FORCE' to proceed with unmerged branch:</ask>
        <check if="user input != 'FORCE'">
          <output>Cleanup aborted.</output>
          <action>HALT</action>
        </check>
        <output>Proceeding with force cleanup...</output>
        <variable>confirmed_unmerged = true</variable>
      </branch>

      <branch if="user chooses keep branch">
        <variable>delete_branch = false</variable>
        <output>Will keep branch {{branch_name}} after removing worktree.</output>
      </branch>
    </check>

    <check if="branch is merged">
      <output>✅ Branch is merged to {{base_branch}} - safe to remove</output>
    </check>
  </check>
</substep>

</step>

<step n="4" goal="Remove worktree" tag="remove-worktree">

<output>Removing worktree at {{worktree_path}}...</output>

<action>Run: git worktree remove {{worktree_path}}</action>

<check if="remove failed">
  <output>❌ Failed to remove worktree: {{error_message}}

This may happen if:
- Worktree directory is locked or in use
- Permission issues

Try forcing removal:
```
git worktree remove --force {{worktree_path}}
```

Or manually:
```
rm -rf {{worktree_path}}
git worktree prune
```
</output>
  <action>HALT</action>
</check>

<output>✅ Worktree removed successfully</output>

</step>

<step n="5" goal="Delete branch (if requested)" tag="delete-branch">

<check if="{{delete_branch}} is true">
  <output>Deleting branch {{branch_name}}...</output>

  <action>Run: git branch -d {{branch_name}}</action>

  <check if="delete failed (unmerged)">
    <output>⚠️ Cannot delete unmerged branch with -d

Use force delete? (This will permanently lose commits not in {{base_branch}})</output>
    <ask>Force delete branch? (yes/no)</ask>

    <branch if="user says yes">
      <action>Run: git branch -D {{branch_name}}</action>
      <check if="force delete succeeded">
        <output>✅ Branch {{branch_name}} force-deleted</output>
      </check>
    </branch>

    <branch if="user says no">
      <output>Branch {{branch_name}} kept. You can delete it later with:
```
git branch -D {{branch_name}}
```
</output>
    </branch>
  </check>

  <check if="delete succeeded">
    <output>✅ Branch {{branch_name}} deleted</output>
  </check>

  <check if="delete failed (other reason)">
    <output>⚠️ Failed to delete branch: {{error_message}}

Branch remains in repository. Delete manually if needed:
```
git branch -d {{branch_name}}  # or -D to force
```
</output>
  </check>
</check>

<check if="{{delete_branch}} is false">
  <output>ℹ️ Branch {{branch_name}} kept as requested</output>
</check>

</step>

<step n="6" goal="Update state tracking" tag="state-update">

<action>Load {state_file}</action>
<action>Remove entry worktrees.{{worktree_name}}</action>
<action>Save {state_file}</action>

<output>✅ State tracking updated</output>

</step>

<step n="7" goal="Prune stale entries (if in prune mode)" tag="prune-stale">

<anchor id="prune_stale" />

<check if="{{prune}} is true OR cleanup_mode == prune_stale">
  <output>Pruning stale worktree tracking entries...</output>

  <action>Run: git worktree list --porcelain</action>
  <action>Get list of active worktree paths</action>

  <action>Load {state_file}</action>
  <action>Compare tracked worktrees with active worktrees</action>
  <action>Find entries in state that don't exist in git worktree list</action>

  <check if="no stale entries found">
    <output>✅ No stale entries found. All tracking is up to date.</output>
    <action>HALT</action>
  </check>

  <output>**Stale entries found:**

{{#each stale_entries}}
- {{name}} ({{path}})
{{/each}}

Remove these entries from tracking?</output>

  <ask>Confirm removal (yes/no):</ask>

  <check if="user says yes">
    <action>Remove stale entries from {state_file}</action>
    <action>Save {state_file}</action>
    <output>✅ {{stale_count}} stale entries removed from tracking</output>
  </check>

  <check if="user says no">
    <output>Prune cancelled. Stale entries kept.</output>
  </check>

  <check if="cleanup_mode == prune_stale">
    <action>HALT</action>
  </check>
</check>

</step>

<step n="8" goal="Display cleanup summary" tag="output">

<output>
---

**🗑️ Cleanup Complete, {user_name}!**

**Removed:**
- ✅ Worktree: `{{worktree_path}}`
{{#if delete_branch}}- ✅ Branch: {{branch_name}}{{else}}- ℹ️ Branch kept: {{branch_name}}{{/if}}
- ✅ State tracking entry

{{#if story_key}}
**BMM Integration:**
Story {{story_key}} worktree has been cleaned up.
If story is complete, mark it as done:
```
/bmad:bmm:workflows:story-done {{story_key}}
```
{{/if}}

**Remaining worktrees:**
{{#if remaining_count > 0}}
{{remaining_count}} worktree(s) still active. Use `/worktree:status` to view.
{{else}}
No worktrees remaining. All features complete! 🎉
{{/if}}

**Next Steps:**
- View remaining worktrees: `/worktree:status`
- Create new worktree: `/worktree:new`
- Prune stale tracking: `/worktree:cleanup --prune`

**Tip:** Cleanup worktrees promptly after merging to keep your workspace tidy!
</output>

</step>

</workflow>
