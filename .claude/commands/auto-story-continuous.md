---
description: 'Continuous autonomous story execution: process all pending stories with auto-retry, commit/push between stories, zero user interaction'
---

# auto-story-continuous

You are orchestrating a **fully autonomous continuous story execution workflow** that processes multiple stories sequentially without user intervention. This workflow executes the complete story lifecycle (create → context → validate → implement → review → commit/push) for each story, automatically handling failures through intelligent retry logic and skipping blocked stories to continue processing.

## 🎯 Core Principles

1. **ZERO USER INTERACTION**: Never pause for user input. All decisions are autonomous.
2. **AUTO-RETRY THEN SKIP**: Failures trigger intelligent retry logic, then skip story if unresolvable.
3. **GIT INTEGRATION**: Automatically commit and push after each approved story.
4. **CONTINUOUS PROGRESS**: One story's failure doesn't halt the entire run.
5. **FULL TRACEABILITY**: Every decision, retry, and outcome is logged.

## ⚙️ Configuration

Use these defaults (embedded in workflow logic):

```yaml
continuous_config:
  # Story selection
  max_stories: null                          # Process all pending stories (null = unlimited)
  epic_filter: null                          # Process all epics (or ["epic-3", "epic-4"])
  status_filter:                             # Process stories in these states
    - "ready-for-dev"
    - "in-progress"
    - "review"
    - "drafted"
    - "backlog"

  # Retry limits
  max_validation_attempts: 3                 # Context validation retry limit
  max_review_cycles: 3                       # Implementation→review loop limit
  max_consecutive_failures: 5                # Pause if 5 stories fail in a row

  # Git behavior
  auto_commit: true
  auto_push: true
  dry_run: false                             # Set true to skip git operations

  # Failure handling (always true for autonomous operation)
  skip_validation_failures: true
  skip_review_failures: true
  skip_blocked_stories: true
  stop_on_git_failure: false

  # Reporting
  verbose_logging: true
  log_file_path: "docs/sprint-artifacts/continuous-run-{timestamp}.yaml"
```

## 🚀 Workflow Execution

### PHASE 0: Pre-Flight Checks

Before starting the continuous run, validate the environment:

1. **Git Status Check**:
   ```bash
   git status
   ```
   - Get current branch name
   - Check for uncommitted changes (warn if many, but continue)
   - If on `main` or `master`: WARN user but continue (they may want to push directly)

2. **Sprint Status Validation**:
   - Read `docs/sprint-artifacts/sprint-status.yaml`
   - Verify file exists and is valid YAML
   - If invalid: HALT with error

3. **Sub-Agent Availability** (conceptual check):
   - Confirm Task tool is available
   - Log that sub-agents will be invoked: bmm-story-creator, bmm-story-context-builder, bmm-story-context-validator, bmm-story-implementer, bmm-story-reviewer

4. **Create Run Tracking File**:
   ```
   run_id = "continuous-run-" + timestamp (YYYYMMDD-HHMMSS)
   log_file = f"docs/sprint-artifacts/{run_id}.yaml"
   ```
   Initialize with:
   ```yaml
   run_id: continuous-run-20251119-141530
   run_started: 2025-11-19T14:15:30Z
   branch: main
   initial_commit: abc123def
   configuration:
     max_stories: null
     max_validation_attempts: 3
     max_review_cycles: 3
     max_consecutive_failures: 5
     auto_commit: true
     auto_push: true
     dry_run: false

   stories_pending: []
   stories_processed: []

   statistics:
     total_stories: 0
     success_count: 0
     blocked_validation_count: 0
     blocked_review_count: 0
     blocked_external_count: 0
     blocked_git_count: 0
     consecutive_failures: 0
   ```

**Output to user:**
```
═══════════════════════════════════════════════════
  CONTINUOUS STORY EXECUTION INITIATED
═══════════════════════════════════════════════════
Branch: main
Run ID: continuous-run-20251119-141530
Log: docs/sprint-artifacts/continuous-run-20251119-141530.yaml

Pre-flight checks: ✅ PASSED
- Git status: Clean
- Sprint status: Valid
- Sub-agents: Available

Starting story processing...
```

---

### PHASE 1: Initialization

1. **Parse Sprint Status**:
   - Read `docs/sprint-artifacts/sprint-status.yaml`
   - Extract all story keys and their current status
   - Filter to stories NOT in `done` status
   - Filter by `status_filter` configuration (ready-for-dev, in-progress, review, drafted, backlog)
   - If `epic_filter` specified, filter to only those epics

2. **Prioritize Stories**:
   Sort stories by status priority:
   1. `ready-for-dev` (highest priority - already contexted and validated)
   2. `in-progress` (may be partially complete)
   3. `review` (needs re-review)
   4. `drafted` (has story file, needs context)
   5. `backlog` (needs full creation workflow)

3. **Apply Limits**:
   - If `max_stories` configured, take first N stories from sorted list
   - Store in `stories_pending` list

4. **Update Tracking File**:
   ```yaml
   stories_pending:
     - 3-5-add-integration-test-with-moneytransfer-example
     - 4-1-implement-signal-point-detection-in-ast
     - 4-2-implement-wait-condition-helper-function

   statistics:
     total_stories: 3
   ```

**Output to user:**
```
Found 3 pending stories:
  1. 3-5-add-integration-test-with-moneytransfer-example (in-progress)
  2. 4-1-implement-signal-point-detection-in-ast (backlog)
  3. 4-2-implement-wait-condition-helper-function (backlog)

Processing stories in sequence...
```

---

### PHASE 2: Main Story Processing Loop

For each story in `stories_pending`, execute the following:

```
FOR story_index, story_key IN ENUMERATE(stories_pending):

    # Initialize story tracking
    story_state = {
        story_key: story_key,
        story_index: story_index + 1,
        total_stories: len(stories_pending),
        current_status: <from sprint-status.yaml>,
        start_time: now(),
        validation_attempts: 0,
        review_cycles: 0,
        phases_completed: [],
        outcome: null,
        failure_reason: null,
        git_commit_sha: null,
        git_push_status: null
    }

    # Output progress header
    OUTPUT:
    """
    ───────────────────────────────────────────────────
    Story {story_index}/{total_stories}: {story_key}
    Current status: {current_status}
    ───────────────────────────────────────────────────
    """

    # Execute single story workflow (detailed below)
    result = EXECUTE_SINGLE_STORY_WORKFLOW(story_state)

    # Handle outcome
    IF result.outcome == "success":
        # Git commit and push
        git_result = EXECUTE_GIT_INTEGRATION(story_state, result)

        # Update sprint-status.yaml
        UPDATE_SPRINT_STATUS(story_key, "done")

        # Log success
        LOG_SUCCESS(story_state, result, git_result)
        statistics.success_count += 1
        statistics.consecutive_failures = 0

        OUTPUT:
        """
        ✅ Story {story_key} COMPLETED
           Duration: {duration}
           Review cycles: {review_cycles}
           Git commit: {git_commit_sha}
           Git push: {git_push_status}

        Moving to next story...
        """

    ELSE IF result.outcome IN ["blocked-validation", "blocked-review", "blocked-external"]:
        # Log blocked story
        LOG_BLOCKED(story_state, result)
        statistics[f"{result.outcome}_count"] += 1
        statistics.consecutive_failures += 1

        OUTPUT:
        """
        ⚠️  Story {story_key} BLOCKED: {result.outcome}
           Reason: {result.failure_reason}
           Duration: {duration}
           Phases completed: {phases_completed}

        Skipping to next story...
        """

        # Check consecutive failure threshold
        IF statistics.consecutive_failures >= max_consecutive_failures:
            OUTPUT:
            """
            ⛔ PAUSING: {max_consecutive_failures} consecutive failures detected

            This suggests a systemic issue. Review the log file:
            {log_file_path}

            Last {max_consecutive_failures} stories all failed. Common issues:
            - Missing architecture documentation
            - Broken test infrastructure
            - Git authentication problems

            Fix systemic issues and restart continuous run.
            """
            HALT_WORKFLOW()

    ELSE:
        # Unknown error
        LOG_ERROR(story_state, result)
        statistics.consecutive_failures += 1

    # Update tracking file after each story
    UPDATE_TRACKING_FILE(story_state, result)

# End of main loop
```

---

### PHASE 3: Single Story Execution Workflow

This is the core autonomous workflow for a single story. It includes all retry logic.

```python
FUNCTION EXECUTE_SINGLE_STORY_WORKFLOW(story_state):

    story_key = story_state.story_key
    current_status = story_state.current_status

    # ─────────────────────────────────────────────────
    # PHASE 3.1: Story Creation (if needed)
    # ─────────────────────────────────────────────────

    IF current_status == "backlog":
        OUTPUT: "  📝 Creating story from backlog..."

        result = INVOKE_SUBAGENT(
            subagent_type="bmm-story-creator",
            description="Create next story",
            prompt=f"Execute create-story workflow autonomously for story {story_key}. Return structured results including story key, file path, and summary."
        )

        IF result.failed:
            RETURN {outcome: "error", failure_reason: "Story creation failed: " + result.error}

        story_state.phases_completed.append("create")
        OUTPUT: f"  ✅ Story created: {result.story_file_path}"

    ELSE:
        # Story already exists, load from file
        story_file_path = f"docs/sprint-artifacts/stories/{story_key}.md"
        OUTPUT: f"  📄 Loading existing story: {story_file_path}"
        story_state.phases_completed.append("load")

    # ─────────────────────────────────────────────────
    # PHASE 3.2: Story Context Building
    # ─────────────────────────────────────────────────

    OUTPUT: "  🔍 Building story context..."

    result = INVOKE_SUBAGENT(
        subagent_type="bmm-story-context-builder",
        description="Build story context",
        prompt=f"Execute story-context workflow autonomously for story {story_key}. Gather all relevant documentation, code, and artifacts. Return context file path and validation status."
    )

    IF result.failed:
        RETURN {outcome: "error", failure_reason: "Context building failed: " + result.error}

    story_state.phases_completed.append("context")
    context_file_path = result.context_file_path
    OUTPUT: f"  ✅ Context built: {context_file_path}"
    IF result.warnings:
        OUTPUT: f"     Warnings: {result.warnings}"

    # ─────────────────────────────────────────────────
    # PHASE 3.3: Story Context Validation (with retry)
    # ─────────────────────────────────────────────────

    validation_passed = False

    WHILE story_state.validation_attempts < max_validation_attempts:
        story_state.validation_attempts += 1
        attempt_num = story_state.validation_attempts

        OUTPUT: f"  ✓ Validating story context (attempt {attempt_num}/{max_validation_attempts})..."

        result = INVOKE_SUBAGENT(
            subagent_type="bmm-story-context-validator",
            description="Validate story context",
            prompt=f"Execute story-context validation autonomously for story {story_key}. Return validation status (PASS/FAIL), issues found, and recommendations."
        )

        IF result.failed:
            # Sub-agent invocation error (not validation failure)
            RETURN {outcome: "error", failure_reason: "Context validation invocation failed: " + result.error}

        # Check validation outcome
        IF result.overall_status == "PASS" OR result.critical_issues == 0:
            validation_passed = True
            story_state.phases_completed.append("validate")
            OUTPUT: f"  ✅ Context validation PASSED"
            IF result.medium_issues > 0:
                OUTPUT: f"     {result.medium_issues} medium issues noted (acceptable)"
            BREAK

        ELSE:
            # Validation FAILED with CRITICAL issues
            OUTPUT: f"  ⚠️  Context validation FAILED (attempt {attempt_num})"
            OUTPUT: f"     Critical issues: {result.critical_issues}"
            FOR issue IN result.critical_issues_list:
                OUTPUT: f"       - {issue}"

            # Retry strategy based on attempt number
            IF attempt_num == 1:
                # Attempt 1 failed: Re-run validator (maybe transient)
                OUTPUT: f"     Retry strategy: Re-run validator"
                CONTINUE  # Loop back to validator

            ELIF attempt_num == 2:
                # Attempt 2 failed: Re-run context builder with expanded search
                OUTPUT: f"     Retry strategy: Re-build context with expanded search"

                result = INVOKE_SUBAGENT(
                    subagent_type="bmm-story-context-builder",
                    description="Re-build story context (expanded)",
                    prompt=f"Execute story-context workflow for {story_key} with EXPANDED search parameters. Cast a wider net for documentation and code artifacts. This is retry attempt {attempt_num} after validation failure."
                )

                IF result.failed:
                    RETURN {outcome: "error", failure_reason: "Context re-building failed: " + result.error}

                OUTPUT: f"     Context rebuilt with expanded search"
                CONTINUE  # Loop back to validator

            ELIF attempt_num == 3:
                # Attempt 3 failed: Re-run context builder with minimal requirements
                OUTPUT: f"     Retry strategy: Re-build context with minimal requirements"

                result = INVOKE_SUBAGENT(
                    subagent_type="bmm-story-context-builder",
                    description="Re-build story context (minimal)",
                    prompt=f"Execute story-context workflow for {story_key} with MINIMAL requirements mode. Accept lower quality context to unblock development. This is final retry attempt."
                )

                IF result.failed:
                    RETURN {outcome: "error", failure_reason: "Context re-building (minimal) failed: " + result.error}

                OUTPUT: f"     Context rebuilt with minimal requirements"
                CONTINUE  # Loop back to validator for final attempt

    # Check if validation ever passed
    IF NOT validation_passed:
        RETURN {
            outcome: "blocked-validation",
            failure_reason: f"Context validation failed after {max_validation_attempts} attempts. Critical issues persist: {result.critical_issues_list}",
            phases_completed: story_state.phases_completed
        }

    # ─────────────────────────────────────────────────
    # PHASE 3.4: Story Implementation (with review loop)
    # ─────────────────────────────────────────────────

    implementation_approved = False

    WHILE story_state.review_cycles < max_review_cycles:
        story_state.review_cycles += 1
        cycle_num = story_state.review_cycles

        # Implementation phase
        OUTPUT: f"  🔨 Implementing story (review cycle {cycle_num}/{max_review_cycles})..."

        IF cycle_num == 1:
            impl_prompt = f"Execute dev-story workflow autonomously for story {story_key}. Implement all acceptance criteria with tests. Return implementation summary, files changed, and test results."
        ELSE:
            impl_prompt = f"Execute dev-story workflow for story {story_key}. This is review cycle {cycle_num} - address code review feedback and fix issues. Focus on CRITICAL and HIGH severity issues first."

        result = INVOKE_SUBAGENT(
            subagent_type="bmm-story-implementer",
            description=f"Implement story (cycle {cycle_num})",
            prompt=impl_prompt
        )

        IF result.failed:
            RETURN {outcome: "error", failure_reason: f"Story implementation failed (cycle {cycle_num}): " + result.error}

        IF cycle_num == 1:
            story_state.phases_completed.append("implement")
        ELSE:
            story_state.phases_completed.append(f"implement-cycle-{cycle_num}")

        OUTPUT: f"  ✅ Implementation complete"
        OUTPUT: f"     Files modified: {result.files_modified}"
        OUTPUT: f"     Tests: {result.test_results}"

        # Review phase
        OUTPUT: f"  👀 Reviewing code (review cycle {cycle_num}/{max_review_cycles})..."

        result = INVOKE_SUBAGENT(
            subagent_type="bmm-story-reviewer",
            description=f"Review story (cycle {cycle_num})",
            prompt=f"Execute code-review workflow autonomously for story {story_key}. Perform senior developer review. Return review outcome (APPROVED/APPROVED_WITH_IMPROVEMENTS/CHANGES REQUESTED/BLOCKED) and issues found."
        )

        IF result.failed:
            RETURN {outcome: "error", failure_reason: f"Code review failed (cycle {cycle_num}): " + result.error}

        story_state.phases_completed.append(f"review-cycle-{cycle_num}")
        review_outcome = result.review_outcome

        # Handle review outcome
        IF review_outcome == "APPROVED":
            implementation_approved = True
            OUTPUT: f"  ✅ Code review APPROVED"
            OUTPUT: f"     Review cycle {cycle_num}: All acceptance criteria validated"
            BREAK

        ELIF review_outcome == "APPROVED_WITH_IMPROVEMENTS":
            OUTPUT: f"  ✅ Code review APPROVED WITH IMPROVEMENTS"
            OUTPUT: f"     Medium issues found: {result.medium_issues}"
            FOR issue IN result.medium_issues_list:
                OUTPUT: f"       - {issue}"
            OUTPUT: f"     Auto-looping to fix MEDIUM issues..."
            # Loop continues - implementer will fix medium issues
            CONTINUE

        ELIF review_outcome == "CHANGES REQUESTED":
            OUTPUT: f"  ⚠️  Code review CHANGES REQUESTED"
            OUTPUT: f"     Critical issues: {result.critical_issues}"
            OUTPUT: f"     High issues: {result.high_issues}"
            FOR issue IN result.critical_issues_list + result.high_issues_list:
                OUTPUT: f"       - {issue}"

            IF cycle_num < max_review_cycles:
                OUTPUT: f"     Auto-looping to fix issues (cycle {cycle_num}/{max_review_cycles})..."
                CONTINUE
            ELSE:
                # Max cycles reached
                RETURN {
                    outcome: "blocked-review",
                    failure_reason: f"Code review requested changes after {max_review_cycles} implementation cycles. Critical/High issues persist: {result.critical_issues_list + result.high_issues_list}",
                    phases_completed: story_state.phases_completed
                }

        ELIF review_outcome == "BLOCKED":
            OUTPUT: f"  ⛔ Code review BLOCKED"
            OUTPUT: f"     Blocker: {result.blocker_reason}"
            RETURN {
                outcome: "blocked-external",
                failure_reason: f"Code review blocked by external dependency or issue: {result.blocker_reason}",
                phases_completed: story_state.phases_completed
            }

        ELSE:
            # Unknown review outcome
            RETURN {
                outcome: "error",
                failure_reason: f"Unknown review outcome: {review_outcome}",
                phases_completed: story_state.phases_completed
            }

    # Check if implementation ever got approved
    IF NOT implementation_approved:
        RETURN {
            outcome: "blocked-review",
            failure_reason: f"Story not approved after {max_review_cycles} review cycles",
            phases_completed: story_state.phases_completed
        }

    # ─────────────────────────────────────────────────
    # SUCCESS: All phases complete
    # ─────────────────────────────────────────────────

    RETURN {
        outcome: "success",
        phases_completed: story_state.phases_completed,
        review_cycles: story_state.review_cycles,
        validation_attempts: story_state.validation_attempts,
        files_changed: result.files_changed,
        test_results: result.test_results
    }
```

---

### PHASE 4: Git Integration

After a story is successfully approved, commit and push changes:

```python
FUNCTION EXECUTE_GIT_INTEGRATION(story_state, result):

    story_key = story_state.story_key

    IF dry_run == true:
        OUTPUT: "  🔍 DRY RUN MODE: Skipping git commit/push"
        RETURN {commit_sha: "dry-run", push_status: "skipped"}

    OUTPUT: "  📦 Committing changes..."

    # Get story details for commit message
    story_file = f"docs/sprint-artifacts/stories/{story_key}.md"
    story_title = EXTRACT_TITLE_FROM_STORY_FILE(story_file)
    story_summary = EXTRACT_SUMMARY_FROM_STORY_FILE(story_file)
    ac_list = EXTRACT_AC_LIST_FROM_STORY_FILE(story_file)

    # Build structured commit message
    commit_message = f"""[Story {story_key}] {story_title}

{story_summary}

Implementation:
{format_ac_list_as_bullets(ac_list)}

Files changed: {len(result.files_changed)}
Tests: {result.test_results}
Review: APPROVED (cycle {story_state.review_cycles})

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    # Stage all changes
    git_add_result = EXECUTE_BASH("git add -A")

    IF git_add_result.failed:
        OUTPUT: f"  ⚠️  Git add failed: {git_add_result.error}"
        RETURN {commit_sha: null, push_status: "failed-add", error: git_add_result.error}

    # Commit with structured message
    git_commit_result = EXECUTE_BASH(f"""git commit -m "$(cat <<'EOF'
{commit_message}
EOF
)"
""")

    IF git_commit_result.failed:
        OUTPUT: f"  ⚠️  Git commit failed: {git_commit_result.error}"
        RETURN {commit_sha: null, push_status: "failed-commit", error: git_commit_result.error}

    # Extract commit SHA
    commit_sha = EXTRACT_SHA_FROM_GIT_OUTPUT(git_commit_result.output)
    OUTPUT: f"  ✅ Committed: {commit_sha[:7]}"

    # Push to remote
    OUTPUT: "  ⬆️  Pushing to remote..."

    current_branch = EXECUTE_BASH("git branch --show-current").output.strip()
    git_push_result = EXECUTE_BASH(f"git push origin {current_branch}")

    IF git_push_result.failed:
        OUTPUT: f"  ⚠️  Git push failed: {git_push_result.error}"
        OUTPUT: f"     Changes are committed locally ({commit_sha[:7]})"
        OUTPUT: f"     You may need to push manually or fix remote authentication"
        RETURN {commit_sha: commit_sha, push_status: "failed-push", error: git_push_result.error}

    OUTPUT: f"  ✅ Pushed to {current_branch}"

    RETURN {commit_sha: commit_sha, push_status: "success"}
```

---

### PHASE 5: Progress Tracking & Logging

Update the tracking file after each story:

```python
FUNCTION UPDATE_TRACKING_FILE(story_state, result):

    # Load current tracking file
    tracking = LOAD_YAML(log_file_path)

    # Build story entry
    story_entry = {
        "story_key": story_state.story_key,
        "status": result.outcome,
        "start_time": story_state.start_time,
        "end_time": now(),
        "duration_seconds": (now() - story_state.start_time).total_seconds(),
        "phases_completed": story_state.phases_completed,
        "validation_attempts": story_state.validation_attempts,
        "review_cycles": story_state.review_cycles
    }

    IF result.outcome == "success":
        story_entry["git_commit_sha"] = result.git_commit_sha
        story_entry["git_push_status"] = result.git_push_status
        story_entry["files_changed"] = len(result.files_changed)
        story_entry["test_results"] = result.test_results

    ELSE:
        story_entry["failure_reason"] = result.failure_reason

    # Append to processed list
    tracking.stories_processed.append(story_entry)

    # Update statistics
    tracking.statistics.total_stories = len(tracking.stories_processed)
    # (success_count, blocked_*_count, consecutive_failures updated in main loop)

    # Save tracking file
    SAVE_YAML(log_file_path, tracking)
```

```python
FUNCTION UPDATE_SPRINT_STATUS(story_key, new_status):

    # Load sprint-status.yaml
    sprint_status = LOAD_YAML("docs/sprint-artifacts/sprint-status.yaml")

    # Find and update story status
    IF story_key IN sprint_status.development_status:
        sprint_status.development_status[story_key] = new_status

    # Save sprint-status.yaml
    SAVE_YAML("docs/sprint-artifacts/sprint-status.yaml", sprint_status)

    OUTPUT: f"  ✅ Updated sprint-status.yaml: {story_key} → {new_status}"
```

---

### PHASE 6: Final Reporting

After all stories processed, generate comprehensive summary:

```python
FUNCTION GENERATE_FINAL_REPORT():

    # Load tracking file
    tracking = LOAD_YAML(log_file_path)

    # Calculate statistics
    total_duration = (now() - tracking.run_started).total_seconds()
    total_duration_formatted = format_duration(total_duration)

    success_stories = [s for s in tracking.stories_processed if s.status == "success"]
    blocked_validation = [s for s in tracking.stories_processed if s.status == "blocked-validation"]
    blocked_review = [s for s in tracking.stories_processed if s.status == "blocked-review"]
    blocked_external = [s for s in tracking.stories_processed if s.status == "blocked-external"]
    blocked_git = [s for s in tracking.stories_processed if s.git_push_status and "failed" in s.git_push_status]

    # Count git commits
    git_commits = sum(1 for s in success_stories if s.git_commit_sha)
    git_pushes = sum(1 for s in success_stories if s.git_push_status == "success")

    # Output final report
    OUTPUT:
    """
    ═══════════════════════════════════════════════════
      CONTINUOUS RUN COMPLETE
    ═══════════════════════════════════════════════════
    Run ID: {tracking.run_id}
    Duration: {total_duration_formatted}
    Branch: {tracking.branch}

    Stories processed: {len(tracking.stories_processed)}

    ✅ Completed successfully: {len(success_stories)}
    ⚠️  Blocked - validation: {len(blocked_validation)}
    ⚠️  Blocked - review: {len(blocked_review)}
    ⚠️  Blocked - external: {len(blocked_external)}
    ⚠️  Blocked - git: {len(blocked_git)}

    Git commits: {git_commits}
    Git pushes: {git_pushes} to branch '{tracking.branch}'

    ───────────────────────────────────────────────────
    SUCCESSFUL STORIES:
    """

    FOR story IN success_stories:
        OUTPUT:
        """
    ✅ {story.story_key}
       Duration: {format_duration(story.duration_seconds)}
       Review cycles: {story.review_cycles}
       Commit: {story.git_commit_sha[:7]}
        """

    IF len(blocked_validation) > 0:
        OUTPUT:
        """
    ───────────────────────────────────────────────────
    BLOCKED - VALIDATION:
        """
        FOR story IN blocked_validation:
            OUTPUT:
            """
    ⚠️  {story.story_key}
       Reason: {story.failure_reason}
       Attempts: {story.validation_attempts}
            """

    IF len(blocked_review) > 0:
        OUTPUT:
        """
    ───────────────────────────────────────────────────
    BLOCKED - REVIEW:
        """
        FOR story IN blocked_review:
            OUTPUT:
            """
    ⚠️  {story.story_key}
       Reason: {story.failure_reason}
       Cycles: {story.review_cycles}
            """

    IF len(blocked_external) > 0:
        OUTPUT:
        """
    ───────────────────────────────────────────────────
    BLOCKED - EXTERNAL DEPENDENCY:
        """
        FOR story IN blocked_external:
            OUTPUT:
            """
    ⛔ {story.story_key}
       Blocker: {story.failure_reason}
            """

    IF len(blocked_git) > 0:
        OUTPUT:
        """
    ───────────────────────────────────────────────────
    GIT OPERATION FAILURES:
        """
        FOR story IN blocked_git:
            OUTPUT:
            """
    ⚠️  {story.story_key}
       Committed: {story.git_commit_sha[:7] if story.git_commit_sha else "N/A"}
       Push status: {story.git_push_status}
       Note: Changes committed locally, push manually
            """

    OUTPUT:
    """
    ═══════════════════════════════════════════════════

    Detailed log: {tracking.log_file_path}

    Next steps:
    - Review blocked stories and resolve issues
    - Re-run continuous workflow to process remaining stories
    - Manually push any commits that failed to push
    """
```

---

## 🛡️ Safety Mechanisms

### Consecutive Failure Threshold

If `max_consecutive_failures` (default: 5) stories fail in a row, PAUSE and report:

```
⛔ PAUSING: 5 consecutive failures detected

This suggests a systemic issue. Review the log file:
docs/sprint-artifacts/continuous-run-20251119-141530.yaml

Last 5 stories all failed. Common issues:
- Missing architecture documentation
- Broken test infrastructure
- Git authentication problems

Fix systemic issues and restart continuous run.
```

This prevents infinite loops on systemic failures.

### Graceful Interrupt Handling

If user sends Ctrl+C or interrupts:
1. Complete current phase (don't leave story half-implemented)
2. Save current tracking file state
3. Generate partial run report
4. Output: "Run interrupted. Partial results saved to {log_file_path}"

### Pre-Run Git Status Check

Before starting, check git status:
- If on `main` or `master`: WARN but continue
- If many uncommitted changes: WARN but continue
- Log initial commit SHA for reference

### Dry-Run Mode

If `dry_run: true`:
- Execute all phases normally
- Skip git commit/push operations
- Mark stories as done in sprint-status
- Note in log: "dry_run: true"

Useful for testing the workflow without making commits.

---

## 📋 Critical Instructions

### Sub-Agent Invocation

Use the Task tool with appropriate `subagent_type`:

- `bmm-story-creator`: Create story from backlog
- `bmm-story-context-builder`: Build story context XML
- `bmm-story-context-validator`: Validate story context
- `bmm-story-implementer`: Implement story with tests
- `bmm-story-reviewer`: Review story implementation

Example:
```python
Task tool:
  subagent_type: "bmm-story-implementer"
  description: "Implement story (cycle 1)"
  prompt: "Execute dev-story workflow autonomously for story 3-5-add-integration-test. Implement all acceptance criteria with tests. Return implementation summary, files changed, and test results."
```

### Autonomous Decision Making

**NEVER pause for user input.** All decisions are made autonomously:

- Validation fails → Auto-retry with escalating strategies
- Review requests changes → Auto-loop to implementation
- Review blocked → Mark blocked, skip to next story
- Git push fails → Log error, continue to next story

### Error Handling

If any sub-agent invocation FAILS (not validation failure, but actual error):
- Log error details
- Mark story as `error` status
- Skip to next story
- Increment consecutive failures counter

### State Tracking

Track these values throughout execution:
- `story_state.validation_attempts` (increments per retry)
- `story_state.review_cycles` (increments per implementation→review loop)
- `statistics.consecutive_failures` (resets to 0 on success)

### Git Commit Message Format

Always use structured format:
```
[Story {key}] {title}

{summary}

Implementation:
- {AC bullet points}

Files changed: {count}
Tests: {results}
Review: APPROVED (cycle {N})

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Use heredoc to preserve formatting:
```bash
git commit -m "$(cat <<'EOF'
{commit_message}
EOF
)"
```

### Sprint Status Updates

After each successful story:
1. Load `docs/sprint-artifacts/sprint-status.yaml`
2. Update story key from current status → `done`
3. Save file
4. Verify update successful

### Logging

After each story, append to tracking file:
```yaml
stories_processed:
  - story_key: 3-5-add-integration-test
    status: success | blocked-validation | blocked-review | blocked-external | error
    start_time: ISO8601
    end_time: ISO8601
    duration_seconds: 450
    phases_completed: [create, context, validate, implement, review]
    validation_attempts: 1
    review_cycles: 2
    git_commit_sha: abc123def (if success)
    git_push_status: success | failed-push | skipped (if success)
    failure_reason: "..." (if blocked/error)
```

---

## 🎬 Workflow Success Criteria

A continuous run is successful when:

1. ✅ All pending stories processed (done or blocked)
2. ✅ Every successful story committed and pushed
3. ✅ Sprint-status.yaml accurately reflects story statuses
4. ✅ Comprehensive tracking log generated
5. ✅ No stories left in inconsistent state

Blocked stories are NOT failures - they're documented for manual resolution.

---

## 🚦 Execution Start

**BEGIN CONTINUOUS WORKFLOW:**

1. Execute PHASE 0: Pre-Flight Checks
2. Execute PHASE 1: Initialization
3. Execute PHASE 2: Main Story Processing Loop
4. Execute PHASE 6: Final Reporting

**REMEMBER:**
- Zero user interaction
- Auto-retry then skip on failures
- Commit and push after each success
- Track everything in log file
- Keep going until all stories processed

Let's process all pending stories autonomously! 🚀
