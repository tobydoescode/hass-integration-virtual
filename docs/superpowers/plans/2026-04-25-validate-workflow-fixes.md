# Validate Workflow Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the GitHub Actions `validate` workflow pass, including current HACS hard failures and warnings.

**Architecture:** The workflow failure is split between repository metadata managed through GitHub APIs and repository files validated by HACS/Hassfest. Fix file-based validation in the repo, then update GitHub repository settings, then rerun the same workflow to verify.

**Tech Stack:** GitHub Actions, HACS Action, Hassfest, Home Assistant integration manifest JSON, GitHub CLI.

---

### Task 1: Fix Integration Manifest Metadata

**Files:**
- Modify: `custom_components/virtual/manifest.json`

- [ ] **Step 1: Update manifest URLs**

Replace `custom_components/virtual/manifest.json` with:

```json
{
  "domain": "virtual",
  "name": "Virtual",
  "codeowners": [],
  "config_flow": true,
  "documentation": "https://github.com/tobydoescode/hass-integration-virtual",
  "issue_tracker": "https://github.com/tobydoescode/hass-integration-virtual/issues",
  "iot_class": "local_push",
  "version": "0.1.0"
}
```

- [ ] **Step 2: Validate JSON locally**

Run:

```bash
python -m json.tool custom_components/virtual/manifest.json
```

Expected: valid JSON printed and exit code `0`.

- [ ] **Step 3: Commit manifest fix**

Run:

```bash
git add custom_components/virtual/manifest.json
git commit -m "fix: add HACS manifest metadata"
```

Expected: commit succeeds.

### Task 2: Add Repository Description And Topics

**Files:**
- No file changes. This updates GitHub repository metadata.

- [ ] **Step 1: Set repository description**

Run:

```bash
gh repo edit --description "Home Assistant custom integration for virtual devices and entities"
```

Expected: command exits `0`.

- [ ] **Step 2: Add HACS/Home Assistant topics**

Run:

```bash
gh repo edit --add-topic home-assistant --add-topic hacs --add-topic home-assistant-integration --add-topic custom-component
```

Expected: command exits `0`.

- [ ] **Step 3: Verify repository metadata**

Run:

```bash
gh repo view --json description,repositoryTopics
```

Expected:

```json
{
  "description": "Home Assistant custom integration for virtual devices and entities",
  "repositoryTopics": {
    "nodes": [
      {"topic": {"name": "home-assistant"}},
      {"topic": {"name": "hacs"}},
      {"topic": {"name": "home-assistant-integration"}},
      {"topic": {"name": "custom-component"}}
    ]
  }
}
```

Topic order may differ.

### Task 3: Add Local Brand Icon

**Files:**
- Create: `custom_components/virtual/brand/icon.png`

- [ ] **Step 1: Create brand directory**

Run:

```bash
mkdir -p custom_components/virtual/brand
```

Expected: directory exists.

- [ ] **Step 2: Add PNG icon**

Create `custom_components/virtual/brand/icon.png` as a square PNG, preferably `256x256` or larger. Use a simple Virtual integration mark that remains readable at small sizes.

Recommended design: a dark rounded-square background with a bright outlined cube or layered squares, avoiding Home Assistant trademarks.

- [ ] **Step 3: Verify PNG file**

Run:

```bash
file custom_components/virtual/brand/icon.png
```

Expected output includes `PNG image data`.

- [ ] **Step 4: Commit brand icon**

Run:

```bash
git add custom_components/virtual/brand/icon.png
git commit -m "chore: add HACS brand icon"
```

Expected: commit succeeds.

### Task 4: Run Local Checks

**Files:**
- No planned file changes.

- [ ] **Step 1: Run lint**

Run:

```bash
uv run ruff check custom_components/ tests/
```

Expected: `All checks passed!`

- [ ] **Step 2: Run format check**

Run:

```bash
uv run ruff format --check custom_components/ tests/
```

Expected: all files already formatted.

- [ ] **Step 3: Run tests**

Run:

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

### Task 5: Re-run Validate Workflow

**Files:**
- No planned file changes.

- [ ] **Step 1: Push commits**

Run:

```bash
git push
```

Expected: push succeeds and starts the `HACS Validation` workflow.

- [ ] **Step 2: Watch latest workflow run**

Run:

```bash
gh run list --workflow validate.yml --limit 1
```

Copy the latest run ID, then run:

```bash
gh run watch <run-id>
```

Expected: workflow completes.

- [ ] **Step 3: Inspect failures if any remain**

Run:

```bash
gh run view <run-id> --log-failed
```

Expected after all fixes: no failed logs because the validate workflow passes.

---

## Self-Review

Spec coverage:
- Missing `issue_tracker`: covered by Task 1.
- Wrong documentation URL: covered by Task 1.
- Missing repository description: covered by Task 2.
- Missing repository topics: covered by Task 2.
- Missing brand icon warning: covered by Task 3.
- Workflow verification: covered by Task 5.

No placeholder tasks remain. The only creative choice is the brand icon artwork, bounded by exact file path, format, and design constraints.
