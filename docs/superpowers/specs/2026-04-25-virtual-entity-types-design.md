# Virtual Entity Types Design

## Context

The current Virtual integration supports one config entry per virtual device and
only switch entities. The next version will add the first batch of useful
virtual entity types:

- `switch`
- `binary_sensor`
- `sensor`
- `button`
- `light`
- `number`
- `select`
- `text`
- `date`
- `datetime`
- `time`

The current MVP config entry data uses a switch-specific `switches` list. No
backward compatibility or migration is required because the integration is still
early and not used by others.

## Goals

- Replace the switch-specific config entry model with a generic entity model.
- Add minimal support for the first batch of entity types.
- Keep entity keys stable, immutable, and unique across a virtual device.
- Keep one config entry per virtual device.
- Preserve device grouping behavior through existing device info and connection
  handling.
- Add a `virtual.set_state` service for updating stateful virtual entities.
- Keep the design extensible for richer per-platform capabilities later.

## Non-Goals

- Full support for every Home Assistant feature on each platform.
- Backward-compatible migration from the MVP `switches` list.
- YAML configuration or YAML reload support.
- Live dynamic config-flow forms that change fields without submitting a step.
- Support for entity platforms outside the first batch.

## Data Model

Each config entry will store a generic `entities` list instead of `switches`.

Device-level fields remain:

- `name`
- `device_id`
- `connection_type`
- `connection_value`
- `custom_connection_type`
- `entities`

Each entity definition has common fields:

- `type`: Home Assistant platform string.
- `key`: stable unique key within the virtual device.
- `name`: display name.
- `icon`: optional icon.
- `entity_category`: blank, `config`, or `diagnostic`.
- `device_class`: optional platform-specific device class.

The `key` is unique across the entire virtual device, regardless of entity type.
For example, a device cannot have both `sensor.temperature` and
`number.temperature` with key `temperature`. This keeps unique IDs, suggested
entity IDs, service lookup, and hard removal simple.

Unique IDs are derived from:

```text
<device_id>_<entity_key>
```

The suggested object ID is the entity key. Keys and entity types are immutable
after creation.

## Type-Specific Minimal Fields

The first implementation will support minimal, useful state only.

### `switch`

- `initial_value`: boolean

Implements normal switch turn on/off services.

### `binary_sensor`

- `initial_value`: boolean

Read-only from Home Assistant's native platform perspective. Can be updated by
options-flow edits or `virtual.set_state`.

### `sensor`

- `value_type`: `string` or `number`
- `initial_value`: string or numeric text, coerced according to `value_type`
- `native_unit_of_measurement`: optional
- `state_class`: optional

Read-only from Home Assistant's native platform perspective. Can be updated by
options-flow edits or `virtual.set_state`.

### `button`

No stateful value. Implements normal button press behavior. Presses update a
`last_pressed` attribute with the current ISO timestamp. Button is excluded from
`virtual.set_state`.

### `light`

- `initial_value`: boolean
- `brightness`: optional integer from 1 to 255

Implements normal light turn on/off services. Brightness support is minimal and
does not include color modes, effects, transitions, or profiles.

### `number`

- `initial_value`: number
- `min`: number
- `max`: number
- `step`: number
- `native_unit_of_measurement`: optional
- `mode`: Home Assistant number mode

Implements normal number set-value service.

### `select`

- `options`: list of strings
- `initial_value`: one of the options

Implements normal select option service.

### `text`

- `initial_value`: string
- `min`: integer
- `max`: integer
- `mode`: Home Assistant text mode

Implements normal text set-value service.

### `date`

- `initial_value`: ISO date string

Implements normal date set-value behavior.

### `time`

- `initial_value`: ISO time string

Implements normal time set-value behavior.

### `datetime`

- `initial_value`: ISO datetime string

Implements normal datetime set-value behavior.

## State Behavior

Stateful entities use Home Assistant restore state.

The configured initial value is used only when no restored state exists. After an
entity has existed and Home Assistant has stored state for it, restore state wins
over the configured initial value.

`button` is stateless and does not restore state.

## Config Flow

Initial setup still creates one virtual device per config entry.

The device details step remains:

- device name
- optional virtual device ID override
- connection type: `none`, `mac`, `custom`
- connection value fields as needed

The entity loop replaces the switch loop:

1. `entity_menu`: ask whether to add an entity.
2. `add_entity_type`: select the entity type.
3. `add_entity`: show a type-specific minimal form.
4. Repeat until the user finishes.

Empty devices remain allowed.

Validation requirements:

- Reject duplicate device IDs across config entries.
- Reject duplicate entity keys across all entity types on the same device.
- Validate type-specific fields:
  - `sensor` numeric values parse as numbers when `value_type` is `number`.
  - `number` min, max, step, and initial value are coherent.
  - `select` options are non-empty and include the initial value.
  - `text` min and max are coherent and initial value length is valid.
  - date, time, and datetime values parse successfully.
  - `light` brightness is blank or between 1 and 255.

Home Assistant config flows do not support robust live field replacement within
one form, so type selection and type-specific fields are separate submitted
steps.

## Options Flow

Options flow actions become:

- edit device metadata
- add entity
- edit entity
- remove entity

Adding an entity uses the same type selection and type-specific form as initial
setup.

Editing an entity:

1. Select an existing entity by key/name/type.
2. Show the type-specific form for that entity's type.
3. Keep key and type immutable.
4. Allow editing common metadata and type-specific minimal fields.

Removing entities:

1. Select one or more entity keys.
2. Show a confirmation step.
3. Hard-remove matching entity registry entries using platform, domain, and
   unique ID.
4. Update the generic `entities` list.
5. Reload the config entry.

## Runtime Architecture

`PLATFORMS` will expand to:

```python
[
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TEXT,
    Platform.DATE,
    Platform.DATETIME,
    Platform.TIME,
]
```

Each Home Assistant platform gets a focused platform file:

- `switch.py`
- `binary_sensor.py`
- `sensor.py`
- `button.py`
- `light.py`
- `number.py`
- `select.py`
- `text.py`
- `date.py`
- `datetime.py`
- `time.py`

Shared helpers should cover:

- selecting entity definitions for a platform
- building device info
- building unique IDs
- setting suggested object IDs from keys
- common metadata handling
- type-specific value coercion
- lookup for `virtual.set_state`

Platform files should remain thin and focused on the Home Assistant entity API
for that platform.

## `virtual.set_state` Service

The integration will register a `virtual.set_state` service.

The service uses Home Assistant's normal target selector and a generic `value`
field:

```yaml
service: virtual.set_state
target:
  entity_id: sensor.virtual_temperature
data:
  value: 21.5
```

The service supports all stateful virtual entity types:

- `switch`
- `binary_sensor`
- `sensor`
- `light`
- `number`
- `select`
- `text`
- `date`
- `datetime`
- `time`

The service rejects `button`.

Values are coerced according to entity type and config before state is written.
Invalid values should raise a Home Assistant service validation error and leave
the entity state unchanged.

## Testing

Tests should cover:

- Generic entity key generation.
- Duplicate key rejection across all entity types.
- Platform lookup by entity type.
- Value coercion for each minimal type.
- Config flow creation with no entities.
- Config flow add for every supported entity type.
- Config flow validation errors for each type with meaningful constraints.
- Options flow add for every supported entity type.
- Options flow edit for every supported entity type.
- Options flow hard removal across multiple platforms.
- Runtime setup for every platform with correct unique IDs and device info.
- Restore state fallback for stateful entities.
- Native service behavior for writable entities.
- Button press behavior.
- `virtual.set_state` updates supported entity types.
- `virtual.set_state` rejects button and invalid values.

## Documentation

README should list supported entity types and include examples for:

- creating a virtual device with entities
- changing state through native Home Assistant services
- changing read-only entity state through `virtual.set_state`

## Implementation Notes

- Prefer Home Assistant platform enums/constants for device classes, modes, and
  state classes where available.
- Keep the storage model declarative so future YAML support can create the same
  definitions.
- Keep identity separate from display names. Renaming an entity should not
  change its key, unique ID, or entity registry identity.
- Avoid full light color/effect support in this batch.
