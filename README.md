# Home Assistant Virtual Integration

Home Assistant custom integration for creating virtual devices and entities for
testing purposes.

## Features

- Create one virtual device per config entry.
- Add zero or more switch entities during setup.
- Add, edit, and hard-remove switches from the config entry options flow.
- Restore virtual switch on/off state across Home Assistant restarts.
- Optionally set a device connection (`none`, `mac`, or `custom`) for Home
  Assistant device-registry grouping.
- Configure switch icon, entity category, and switch device class.

Only switch entities are supported in v1. The internal data model uses stable
device IDs and switch keys so YAML import/reload support can be added later.

## Installation

Install manually by copying `custom_components/virtual` into your Home Assistant
`custom_components` directory, then restart Home Assistant.

For HACS, add this repository as a custom integration repository and install the
`Virtual` integration.

## Development

Install dependencies:

```bash
uv sync --all-extras
```

Run tests:

```bash
uv run pytest tests/ -v
```

Run linting:

```bash
uv run ruff check custom_components/ tests/
uv run ruff format --check custom_components/ tests/
```

Start a local Home Assistant instance with the integration mounted:

```bash
docker compose up -d
```

Then open `http://localhost:8123`.

The devcontainer uses `ghcr.io/home-assistant/devcontainer:2026.4`, forwards
port 8123, and mounts `custom_components/virtual` into the Home Assistant config
directory for manual UI testing.
