# Worktree New Workflow Instructions

<critical>The workflow execution engine is governed by: {project_root}/.bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {installed_path}/workflow.yaml</critical>
<critical>Communicate all responses in {communication_language}</critical>

<workflow>

<step n="1" goal="Gather worktree parameters" tag="input">

<action>Check if parameters provided via arguments:
- {{feature_name}}: Name for the worktree/feature
- {{branch_name}}: Git branch name (optional, auto-generate if not provided)
- {{base_branch}}: Branch to fork from (default: main)
- {{story_key}}: Optional BMM story key for integration
</action>

<check if="{{feature_name}} is null">
  <ask>Do you want to create a worktree for a specific BMM story, or a custom feature?

Options:
1. From BMM story (reads story from sprint status)
2. Custom feature (you provide feature name)
</ask>

  <branch if="user selects BMM story">
    <action>Read {sprint_status}</action>
    <action>Find ALL stories where status is "ready-for-dev" or "drafted"</action>
    <action>Display list of available stories with keys and titles</action>
    <ask>Select story by key or number:</ask>
    <action>Set {{story_key}} from user selection</action>
    <action>Read story file from sprint_artifacts/stories/{{story_key}}.md</action>
    <action>Extract story title and generate feature_name from it (lowercase, hyphenated)</action>
    <action>Auto-generate branch_name as "feature/{{feature_name}}"</action>
  </branch>

  <branch if="user selects custom feature">
    <ask>Enter feature name (will be used for directory and branch):
Example: epic-6-signals, bugfix-validation, refactor-analyzer</ask>
    <action>Set {{feature_name}} from user input</action>
    <action>Auto-generate branch_name as "feature/{{feature_name}}"</action>
  </branch>
</check>

<check if="{{branch_name}} is null">
  <action>Auto-generate branch_name from feature_name: "feature/{{feature_name}}"</action>
</check>

<action>Calculate worktree_path: {worktree_root}/{{feature_name}}</action>
<action>Resolve {worktree_root} template (replace {project-name} with {project_name})</action>

<output>**Worktree Configuration:**

- Feature: {{feature_name}}
- Branch: {{branch_name}}
- Base: {{base_branch}}
- Path: {{worktree_path}}
{{#if story_key}}- Story: {{story_key}}{{/if}}
</output>

<ask>Proceed with worktree creation? (yes/no)</ask>
<check if="user says no">
  <output>Worktree creation cancelled.</output>
  <action>HALT</action>
</check>

</step>

<step n="2" goal="Validate prerequisites" tag="validation">

<action>Check if worktree root parent directory exists</action>
<check if="parent directory does not exist">
  <output>⚠️ Worktree root parent directory does not exist: {{parent_of_worktree_root}}

Creating parent directory...</output>
  <action>Run: mkdir -p {{parent_of_worktree_root}}</action>
</check>

<action>Check if worktree path already exists</action>
<check if="worktree path exists">
  <output>❌ Error: Worktree path already exists: {{worktree_path}}

Please choose a different feature name or remove the existing worktree first.
Use `/worktree:cleanup` to remove old worktrees.</output>
  <action>HALT</action>
</check>

<action>Check if branch already exists locally</action>
<action>Run: git branch --list {{branch_name}}</action>
<check if="branch exists">
  <output>⚠️ Warning: Branch {{branch_name}} already exists locally.

Options:
1. Use existing branch (checkout in worktree)
2. Choose different branch name
3. Cancel

Select option:</output>
  <branch if="user selects option 1">
    <action>Continue with existing branch</action>
  </branch>
  <branch if="user selects option 2">
    <ask>Enter new branch name:</ask>
    <action>Set {{branch_name}} from user input</action>
    <action>Re-check if new branch exists (repeat this check)</action>
  </branch>
  <branch if="user selects option 3">
    <output>Worktree creation cancelled.</output>
    <action>HALT</action>
  </branch>
</check>

<action if="{auto_sync_on_create} == true">Sync base branch with remote</action>
<action if="{auto_sync_on_create} == true">Run: git fetch origin {base_branch}</action>

</step>

<step n="3" goal="Create git worktree" tag="git-worktree">

<output>Creating worktree at {{worktree_path}}...</output>

<action>Run: git worktree add {{worktree_path}} -b {{branch_name}} origin/{{base_branch}}</action>

<check if="command failed">
  <output>❌ Failed to create worktree. Error: {{error_message}}

Common issues:
- Base branch doesn't exist
- Git worktree command not available
- Permission issues

Please resolve the issue and try again.</output>
  <action>HALT</action>
</check>

<output>✅ Worktree created successfully!</output>

</step>

<step n="4" goal="Setup development environment" tag="env-setup">

<check if="{auto_setup_env} == true">
  <output>Setting up development environment...</output>

  <action>Change directory: cd {{worktree_path}}</action>

  <check if="pyproject.toml exists in worktree">
    <output>Python project detected. Setting up virtual environment with {python_env_tool}...</output>

    <action if="{python_env_tool} == 'uv'">Run: cd {{worktree_path}} && uv venv</action>
    <action if="{python_env_tool} == 'uv'">Run: cd {{worktree_path}} && source .venv/bin/activate && uv sync</action>

    <action if="{python_env_tool} == 'venv'">Run: cd {{worktree_path}} && python -m venv .venv</action>
    <action if="{python_env_tool} == 'venv'">Run: cd {{worktree_path}} && source .venv/bin/activate && pip install -e .</action>

    <check if="setup succeeded">
      <output>✅ Python environment setup complete</output>
    </check>
    <check if="setup failed">
      <output>⚠️ Python environment setup failed. You may need to set it up manually:
cd {{worktree_path}}
{python_env_tool} venv && source .venv/bin/activate && {python_env_tool} sync</output>
    </check>
  </check>

  <check if="package.json exists in worktree">
    <output>Node.js project detected. Installing dependencies...</output>
    <action>Run: cd {{worktree_path}} && npm install</action>
    <check if="install succeeded">
      <output>✅ Node.js dependencies installed</output>
    </check>
    <check if="install failed">
      <output>⚠️ npm install failed. You may need to install dependencies manually:
cd {{worktree_path}} && npm install</output>
    </check>
  </check>

</check>

</step>

<step n="5" goal="Update worktree state tracking" tag="state-update">

<action>Load {state_file}</action>
<action>Add new entry under worktrees.{{feature_name}}:
  path: {{worktree_path}}
  branch: {{branch_name}}
  base_branch: {{base_branch}}
  created: {{current_timestamp}}
  last_sync: {{current_timestamp}}
  env_setup: {{env_setup_success}}
  status: active
  {{#if story_key}}story_key: {{story_key}}{{/if}}
</action>
<action>Save {state_file}</action>

</step>

<step n="6" goal="Display success summary" tag="output">

<output>**🎉 Worktree Created Successfully, {user_name}!**

**Worktree Details:**
- **Name:** {{feature_name}}
- **Path:** `{{worktree_path}}`
- **Branch:** {{branch_name}}
- **Base:** {{base_branch}}
{{#if story_key}}- **Story:** {{story_key}}{{/if}}
- **Environment:** {{#if env_setup_success}}✅ Setup complete{{else}}⚠️ Manual setup required{{/if}}

**Next Steps:**

1. **Open in new Claude Code window:**
   ```bash
   cd {{worktree_path}}
   code .  # Or your preferred editor
   ```

2. **Activate environment** (if not auto-setup):
   ```bash
   cd {{worktree_path}}
   source .venv/bin/activate  # Python
   # or
   npm install  # Node.js
   ```

3. **Start development:**
   {{#if story_key}}- Load DEV agent: `/bmad:bmm:agents:dev`
   - Run story workflow: `/bmad:bmm:workflows:dev-story`
   {{else}}- Begin feature development
   - Commit regularly to {{branch_name}}
   {{/if}}

4. **Sync with main** (recommended daily):
   ```bash
   /worktree:sync {{feature_name}}
   ```

5. **When complete:**
   - Merge your branch to main
   - Clean up: `/worktree:cleanup {{feature_name}}`

**Parallel Development:**
- You can now create additional worktrees for other features
- Each worktree is completely isolated
- Use `/worktree:status` to see all active worktrees

**Tips:**
- Keep worktrees short-lived (hours to days, not weeks)
- Sync with main regularly to avoid conflicts
- Use `/worktree:status` to monitor all worktrees
</output>

</step>

</workflow>
