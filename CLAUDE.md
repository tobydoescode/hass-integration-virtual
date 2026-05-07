# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Home Assistant custom integration for creating virtual devices and entities for testing purposes. Supports switch, binary_sensor, sensor, button, light, number, select, text, date, datetime, and time entity types. Distributed via HACS.

## Commands

```bash
task sync                # Install dependencies (uv)
task test                # Run tests
task test:coverage       # Run tests with coverage report
task lint                # Ruff lint + format check
task lint:fix            # Auto-fix lint and formatting
task typecheck           # Run pyright type checker
uv run pyright custom_components/virtual/   # Type check
task dev                 # Start HA in Docker
task dev:restart         # Restart HA after code changes
task dev:logs            # Tail HA logs
```

Run a single test: `uv run pytest tests/test_switch.py::test_name -v`

## Architecture

The integration uses a config-entry-per-device pattern without a coordinator (no hardware or network to poll):

- **`__init__.py`** -- Registers `virtual.set_state`, `virtual.import_yaml`, and `virtual.export_yaml` services. Contains `async_migrate_entry` skeleton for future config entry migrations. Each config entry holds one device definition with zero or more entity definitions.

- **`config_flow.py`** -- Multi-step config flow: user enters device metadata, then adds entities in a loop. Options flow supports editing device metadata, adding/editing/removing entities. Entity removal cleans up the entity registry.

- **`entity.py`** -- `VirtualEntityBase` mixin provides common attributes (`unique_id`, `device_info`, `icon`, etc.) and registers entities in a runtime registry for the `set_state` service. Uses `_attr_has_entity_name = False` because entity names are user-defined, not device-relative.

- **`models.py`** -- Pure validation and coercion helpers. `coerce_entity_value` converts raw input to the correct Python type per entity type. `build_device_info` constructs HA device registry info with optional MAC or custom connections.

- **Platform files** (`switch.py`, `binary_sensor.py`, `sensor.py`, `light.py`, `number.py`, `select.py`, `text.py`, `date.py`, `datetime.py`, `time.py`, `button.py`) -- Each creates entities from config entry data using `RestoreEntity` for state persistence across restarts (except `button.py` which is action-only).

- **`yaml_storage.py`** -- Import/export virtual devices from/to `virtual.yaml`. YAML import is non-destructive: it creates or updates entries but never deletes them. Entities not in YAML are preserved with a warning log.

- **`diagnostics.py`** -- Exposes config entry device/entity metadata for the HA diagnostics panel.

## Key Design Decisions

- No coordinator pattern -- virtual entities have no hardware or network connection, so there is nothing to poll. State is set via services or native HA entity methods.
- Entities use `RestoreEntity` (not `CoordinatorEntity`) to persist state across HA restarts.
- Each config entry is one virtual device. Entity definitions are stored in `entry.data["entities"]` as a list of dicts.
- `_attr_has_entity_name = False` because names are user-supplied strings, not relative to a device name.
- `strings.json` and `translations/en.json` must stay in sync manually.

## Testing

Tests use `MockConfigEntry` from `pytest-homeassistant-custom-component`. Coverage must stay above 90% (enforced in CI). The `conftest.py` auto-cleans `virtual.yaml` between tests and enables custom integrations.

## CI

Two workflows: `ci.yml` (ruff, pyright, pytest with coverage artifact) and `validate.yaml` (HACS + hassfest validation). Pre-commit runs ruff check/format and gitleaks.
