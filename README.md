# Home Assistant Virtual Integration

[![HACS Validation](https://github.com/tobydoescode/hass-integration-virtual/actions/workflows/validate.yaml/badge.svg)](https://github.com/tobydoescode/hass-integration-virtual/actions/workflows/validate.yaml)
[![CI](https://github.com/tobydoescode/hass-integration-virtual/actions/workflows/ci.yml/badge.svg)](https://github.com/tobydoescode/hass-integration-virtual/actions/workflows/ci.yml)

Home Assistant custom integration for creating virtual devices and entities for
testing purposes.

## Features

- Create one virtual device per config entry.
- Add zero or more virtual entities during setup.
- Add, edit, and hard-remove entities from the config entry options flow.
- Supports `switch`, `binary_sensor`, `sensor`, `button`, `light`, `number`,
  `select`, `text`, `date`, `datetime`, and `time` entities.
- Restore supported virtual entity state across Home Assistant restarts.
- Set entity state through the `virtual.set_state` service. Button entities are
  action-only and are not supported by this service.
- Optionally set a device connection (`none`, `mac`, or `custom`) for Home
  Assistant device-registry grouping.
- Configure entity icon, entity category, device class, and type-specific
  options such as units, state class, ranges, options, modes, and brightness.
- Import and export virtual device definitions with `virtual.yaml`.

Example service call:

```yaml
service: virtual.set_state
target:
  entity_id: sensor.virtual_temperature
data:
  value: "21.5"
```

## YAML import and export

The integration reads `virtual.yaml` from the Home Assistant config directory
when Home Assistant starts and when Virtual config entries are set up or
reloaded. YAML changes are not watched live.

Use the `virtual.import_yaml` service to manually import `virtual.yaml` and
reload changed entries. Use `virtual.export_yaml` to write the current Virtual
config entries back to `virtual.yaml`.

Import is non-destructive. Devices in `virtual.yaml` are matched to existing
Virtual config entries by `device_id`; entities are matched by `key`. Matching
devices/entities are updated and missing devices/entities are created. Existing
Virtual devices or entities that are absent from the YAML file are left alone,
with warning logs noting that they are not managed by `virtual.yaml`.

Example `virtual.yaml`:

```yaml
devices:
  - name: YAML Device
    device_id: virtual_yaml
    connection_type: none
    entities:
      - type: switch
        name: YAML Switch
        key: yaml_switch
        initial_value: true
```

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
