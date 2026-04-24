# Virtual Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a HACS/manual Home Assistant custom integration that creates virtual devices and switch entities through config and options flows.

**Architecture:** One config entry represents one virtual device. Config entry data stores stable device and switch definitions; switch runtime state is restored by Home Assistant. Options flow edits device metadata, adds/edits switches, and hard-removes deleted switch entity registry entries.

**Tech Stack:** Home Assistant custom integration APIs, `pytest-homeassistant-custom-component`, Ruff, uv, Docker Compose, devcontainer.

---

### Task 1: Repository Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `Taskfile.yml`
- Create: `.devcontainer/devcontainer.json`
- Create: `docker-compose.yml`
- Create: `hacs.json`
- Create: `.pre-commit-config.yaml`
- Create: `.github/workflows/validate.yml`
- Create: `renovate.json`
- Create: `.gitignore`

- [ ] Add tooling files modeled on `/Users/toby/Code/home/ha/hass-integration-kubernetes`.
- [ ] Run `uv sync --all-extras`.

### Task 2: Definition Helpers With Tests

**Files:**
- Create: `tests/test_definitions.py`
- Create: `custom_components/virtual/const.py`
- Create: `custom_components/virtual/models.py`

- [ ] Write tests for generated device IDs, slug switch keys, duplicate detection, MAC normalization, and device info connections.
- [ ] Run `uv run pytest tests/test_definitions.py -v` and verify failure because implementation is missing.
- [ ] Implement constants and model/helper functions.
- [ ] Run `uv run pytest tests/test_definitions.py -v` and verify pass.

### Task 3: Config Flow With Tests

**Files:**
- Create: `tests/test_config_flow.py`
- Create: `custom_components/virtual/config_flow.py`
- Create: `custom_components/virtual/manifest.json`
- Create: `custom_components/virtual/strings.json`
- Create: `custom_components/virtual/translations/en.json`

- [ ] Write tests for empty device creation, switch loop creation, duplicate device ID rejection, duplicate switch key rejection, and connection validation.
- [ ] Run `uv run pytest tests/test_config_flow.py -v` and verify failure because config flow is missing.
- [ ] Implement config flow.
- [ ] Run `uv run pytest tests/test_config_flow.py -v` and verify pass.

### Task 4: Switch Platform And Setup With Tests

**Files:**
- Create: `tests/test_switch.py`
- Create: `custom_components/virtual/__init__.py`
- Create: `custom_components/virtual/switch.py`

- [ ] Write tests for switch entity setup, unique IDs, device info, turn on/off, and state restoration.
- [ ] Run `uv run pytest tests/test_switch.py -v` and verify failure because platform is missing.
- [ ] Implement entry setup/unload and switch entity.
- [ ] Run `uv run pytest tests/test_switch.py -v` and verify pass.

### Task 5: Options Flow With Tests

**Files:**
- Modify: `tests/test_config_flow.py`
- Modify: `custom_components/virtual/config_flow.py`

- [ ] Write tests for options flow add, edit, and hard-remove switch with entity registry cleanup.
- [ ] Run targeted options-flow tests and verify failure.
- [ ] Implement options flow.
- [ ] Run targeted options-flow tests and verify pass.

### Task 6: Final Verification

**Files:**
- Modify: `README.md`

- [ ] Update README with install, devcontainer, Docker Compose, and testing notes.
- [ ] Run `uv run ruff check custom_components/ tests/`.
- [ ] Run `uv run ruff format --check custom_components/ tests/`.
- [ ] Run `uv run pytest tests/ -v`.
