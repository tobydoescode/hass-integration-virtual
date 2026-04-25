# Virtual Entity Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the switch-only virtual entity model with a generic entity model and add minimal support for switch, binary sensor, sensor, button, light, number, select, text, date, datetime, and time entities.

**Architecture:** Config entries will store `entities: [...]`, where each definition has common identity/metadata fields plus type-specific minimal config. Each Home Assistant platform gets a focused platform file backed by shared helpers for definition lookup, metadata, restore-state coercion, and the `virtual.set_state` service. No migration from the MVP `switches` shape is required.

**Tech Stack:** Home Assistant custom integration APIs, config/options flows, RestoreEntity, platform entity classes, pytest-homeassistant-custom-component, Ruff.

---

## File Structure

- Modify `custom_components/virtual/const.py`: replace switch-specific constants with generic entity constants, platform/type mappings, service constants, and supported type lists.
- Modify `custom_components/virtual/models.py`: add generic entity helpers, validation, value coercion, platform filtering, unique ID generation, and common metadata helpers.
- Create `custom_components/virtual/entity.py`: shared base/mixins for virtual entities, including common metadata, suggested object ID, device info, state restoration helpers, and a runtime entity registry for `virtual.set_state`.
- Modify `custom_components/virtual/__init__.py`: expand `PLATFORMS`, register/unregister `virtual.set_state`, keep setup/unload/reload behavior.
- Replace `custom_components/virtual/switch.py`: use generic entity definitions while preserving switch behavior.
- Create platform files: `binary_sensor.py`, `sensor.py`, `button.py`, `light.py`, `number.py`, `select.py`, `text.py`, `date.py`, `datetime.py`, `time.py`.
- Modify `custom_components/virtual/config_flow.py`: replace switch-only flow with generic type selection, type-specific schemas, generic add/edit/remove actions, and hard removal across platforms.
- Modify `custom_components/virtual/strings.json` and `custom_components/virtual/translations/en.json`: update flow and service strings.
- Create `custom_components/virtual/services.yaml`: document `virtual.set_state` service fields.
- Modify tests:
  - `tests/test_definitions.py`
  - `tests/test_config_flow.py`
  - `tests/test_switch.py`
  - create `tests/test_platforms.py`
  - create `tests/test_set_state.py`
- Modify `README.md`: document supported entity types and `virtual.set_state`.

---

### Task 1: Generic Model Constants And Helper Tests

**Files:**
- Modify: `custom_components/virtual/const.py`
- Modify: `custom_components/virtual/models.py`
- Modify: `tests/test_definitions.py`

- [ ] **Step 1: Write failing tests for generic entity helpers**

Add tests in `tests/test_definitions.py` for:

```python
from homeassistant.const import Platform

from custom_components.virtual.const import (
    CONF_ENTITIES,
    CONF_ENTITY_TYPE,
    CONF_INITIAL_VALUE,
    ENTITY_TYPE_BINARY_SENSOR,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_SWITCH,
)
from custom_components.virtual.models import (
    coerce_entity_value,
    entities_for_platform,
    entity_unique_id,
    generate_entity_key,
    validate_unique_entity_key,
)


def test_generate_entity_key_slugs_name_and_avoids_collisions() -> None:
    assert generate_entity_key("Test Entity", {"test_entity", "test_entity_2"}) == "test_entity_3"


def test_validate_unique_entity_key_rejects_duplicate_across_types() -> None:
    with pytest.raises(VirtualValidationError):
        validate_unique_entity_key(
            "temperature",
            [
                {
                    CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR,
                    CONF_KEY: "temperature",
                }
            ],
        )


def test_entities_for_platform_filters_by_type() -> None:
    device = {
        CONF_ENTITIES: [
            {CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH, CONF_KEY: "power"},
            {CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR, CONF_KEY: "temperature"},
        ]
    }

    assert entities_for_platform(device, Platform.SWITCH) == [
        {CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH, CONF_KEY: "power"}
    ]


def test_entity_unique_id_uses_device_id_and_key() -> None:
    assert entity_unique_id("virtual_device", "temperature") == "virtual_device_temperature"


def test_coerce_boolean_value() -> None:
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_BINARY_SENSOR}
    assert coerce_entity_value(definition, "true") is True
    assert coerce_entity_value(definition, False) is False
```

- [ ] **Step 2: Run helper tests and verify failure**

Run:

```bash
uv run pytest tests/test_definitions.py -v
```

Expected: fails because `CONF_ENTITIES`, generic helper functions, and entity type constants do not exist.

- [ ] **Step 3: Implement generic constants and helper shell**

In `custom_components/virtual/const.py`:

```python
CONF_ENTITIES = "entities"
CONF_ENTITY_TYPE = "type"
CONF_INITIAL_VALUE = "initial_value"
CONF_VALUE_TYPE = "value_type"
CONF_NATIVE_UNIT_OF_MEASUREMENT = "native_unit_of_measurement"
CONF_STATE_CLASS = "state_class"
CONF_MIN = "min"
CONF_MAX = "max"
CONF_STEP = "step"
CONF_MODE = "mode"
CONF_OPTIONS = "options"
CONF_BRIGHTNESS = "brightness"

SERVICE_SET_STATE = "set_state"
ATTR_VALUE = "value"

ENTITY_TYPE_SWITCH = Platform.SWITCH.value
ENTITY_TYPE_BINARY_SENSOR = Platform.BINARY_SENSOR.value
ENTITY_TYPE_SENSOR = Platform.SENSOR.value
ENTITY_TYPE_BUTTON = Platform.BUTTON.value
ENTITY_TYPE_LIGHT = Platform.LIGHT.value
ENTITY_TYPE_NUMBER = Platform.NUMBER.value
ENTITY_TYPE_SELECT = Platform.SELECT.value
ENTITY_TYPE_TEXT = Platform.TEXT.value
ENTITY_TYPE_DATE = Platform.DATE.value
ENTITY_TYPE_DATETIME = Platform.DATETIME.value
ENTITY_TYPE_TIME = Platform.TIME.value

SUPPORTED_ENTITY_TYPES = [
    ENTITY_TYPE_SWITCH,
    ENTITY_TYPE_BINARY_SENSOR,
    ENTITY_TYPE_SENSOR,
    ENTITY_TYPE_BUTTON,
    ENTITY_TYPE_LIGHT,
    ENTITY_TYPE_NUMBER,
    ENTITY_TYPE_SELECT,
    ENTITY_TYPE_TEXT,
    ENTITY_TYPE_DATE,
    ENTITY_TYPE_DATETIME,
    ENTITY_TYPE_TIME,
]

PLATFORMS = [
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

In `custom_components/virtual/models.py`, add `generate_entity_key`, `validate_unique_entity_key`, `entities_for_platform`, `entity_unique_id`, and `coerce_entity_value`.

Keep `generate_switch_key`, `validate_unique_switch_key`, and `switch_unique_id` only as temporary compatibility aliases used by existing tests; later tasks can update tests and remove aliases.

- [ ] **Step 4: Run helper tests and verify pass**

Run:

```bash
uv run pytest tests/test_definitions.py -v
```

Expected: all definition tests pass.

---

### Task 2: Type-Specific Value Validation And Coercion

**Files:**
- Modify: `custom_components/virtual/models.py`
- Modify: `tests/test_definitions.py`

- [ ] **Step 1: Write failing value coercion tests**

Add tests covering:

```python
def test_coerce_sensor_number_value() -> None:
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR, CONF_VALUE_TYPE: "number"}
    assert coerce_entity_value(definition, "21.5") == 21.5


def test_coerce_sensor_string_value() -> None:
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR, CONF_VALUE_TYPE: "string"}
    assert coerce_entity_value(definition, 21.5) == "21.5"


def test_coerce_number_rejects_out_of_range() -> None:
    definition = {
        CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER,
        CONF_MIN: 0,
        CONF_MAX: 10,
        CONF_STEP: 1,
    }
    with pytest.raises(VirtualValidationError):
        coerce_entity_value(definition, 11)


def test_coerce_select_rejects_unknown_option() -> None:
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_SELECT, CONF_OPTIONS: ["a", "b"]}
    with pytest.raises(VirtualValidationError):
        coerce_entity_value(definition, "c")


def test_coerce_text_rejects_invalid_length() -> None:
    definition = {CONF_ENTITY_TYPE: ENTITY_TYPE_TEXT, CONF_MIN: 2, CONF_MAX: 4}
    with pytest.raises(VirtualValidationError):
        coerce_entity_value(definition, "abcde")


def test_coerce_date_time_datetime_values() -> None:
    assert str(coerce_entity_value({CONF_ENTITY_TYPE: ENTITY_TYPE_DATE}, "2026-04-25")) == "2026-04-25"
    assert str(coerce_entity_value({CONF_ENTITY_TYPE: ENTITY_TYPE_TIME}, "13:45:00")) == "13:45:00"
    assert coerce_entity_value({CONF_ENTITY_TYPE: ENTITY_TYPE_DATETIME}, "2026-04-25T13:45:00+00:00").isoformat() == "2026-04-25T13:45:00+00:00"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
uv run pytest tests/test_definitions.py -v
```

Expected: fails because type-specific coercion is incomplete.

- [ ] **Step 3: Implement coercion**

Implement:

- boolean coercion for `switch`, `binary_sensor`, and `light`
- numeric coercion for `sensor` with `value_type == "number"` and `number`
- string coercion for `sensor` with `value_type == "string"` and `text`
- option validation for `select`
- ISO parsing for `date`, `time`, and `datetime`
- brightness validation helper for `light`

Use Python standard library `datetime.date.fromisoformat`, `datetime.time.fromisoformat`, and `datetime.datetime.fromisoformat`.

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
uv run pytest tests/test_definitions.py -v
```

Expected: all definition tests pass.

---

### Task 3: Shared Virtual Entity Base And Switch Conversion

**Files:**
- Create: `custom_components/virtual/entity.py`
- Modify: `custom_components/virtual/switch.py`
- Modify: `tests/test_switch.py`
- Modify: `tests/test_definitions.py`

- [ ] **Step 1: Update switch tests to generic `entities` storage**

In `tests/test_switch.py`, change `_entry_data()` to:

```python
return {
    CONF_NAME: "Virtual Device",
    CONF_DEVICE_ID: "virtual_device",
    CONF_CONNECTION_TYPE: CONNECTION_TYPE_MAC,
    CONF_CONNECTION_VALUE: "aa:bb:cc:dd:ee:ff",
    CONF_ENTITIES: [
        {
            CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
            CONF_NAME: "Main Power",
            CONF_KEY: "main_power",
            CONF_ICON: "mdi:power",
            CONF_ENTITY_CATEGORY: "",
            CONF_DEVICE_CLASS: "switch",
            CONF_INITIAL_VALUE: False,
        }
    ],
}
```

Add a test that initial switch state can be `True` when no restore state exists.

- [ ] **Step 2: Run switch tests and verify failure**

Run:

```bash
uv run pytest tests/test_switch.py -v
```

Expected: fails because switch platform still reads `CONF_SWITCHES`.

- [ ] **Step 3: Create shared entity base**

Create `custom_components/virtual/entity.py` with:

- `VirtualEntityBase`
- common `__init__(device, definition)`
- `_attr_name`
- `_attr_unique_id = entity_unique_id(device_id, key)`
- `internal_integration_suggested_object_id = key`
- icon/category/device class handling
- `_attr_device_info = build_device_info(device)`
- optional `async_set_virtual_state(value)` method to be overridden by stateful entities

- [ ] **Step 4: Convert switch platform**

In `switch.py`, use:

```python
entities_for_platform(entry.data, Platform.SWITCH)
```

Use `CONF_INITIAL_VALUE` fallback instead of hard-coded `False`.

Implement `async_set_virtual_state` by coercing a switch value and writing state.

- [ ] **Step 5: Run switch tests and definition tests**

Run:

```bash
uv run pytest tests/test_switch.py tests/test_definitions.py -v
```

Expected: all tests pass.

---

### Task 4: Config Flow Generic Entity Add

**Files:**
- Modify: `custom_components/virtual/config_flow.py`
- Modify: `custom_components/virtual/strings.json`
- Modify: `custom_components/virtual/translations/en.json`
- Modify: `tests/test_config_flow.py`

- [ ] **Step 1: Replace config-flow switch tests with generic entity tests**

Update existing creation tests:

- empty device creates `{CONF_ENTITIES: []}`
- adding switch uses `entity_menu -> add_entity_type -> add_entity`
- duplicate key rejection uses one sensor plus one number with the same key

Add parametrized tests for adding each supported entity type:

```python
@pytest.mark.parametrize(
    ("entity_type", "payload", "expected"),
    [
        (
            ENTITY_TYPE_SWITCH,
            {CONF_NAME: "Power", CONF_KEY: "", CONF_INITIAL_VALUE: True},
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SWITCH,
                CONF_NAME: "Power",
                CONF_KEY: "power",
                CONF_INITIAL_VALUE: True,
            },
        ),
        (
            ENTITY_TYPE_BINARY_SENSOR,
            {CONF_NAME: "Motion", CONF_KEY: "", CONF_INITIAL_VALUE: False},
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_BINARY_SENSOR,
                CONF_NAME: "Motion",
                CONF_KEY: "motion",
                CONF_INITIAL_VALUE: False,
            },
        ),
        (
            ENTITY_TYPE_SENSOR,
            {
                CONF_NAME: "Temperature",
                CONF_KEY: "",
                CONF_VALUE_TYPE: "number",
                CONF_INITIAL_VALUE: "21.5",
                CONF_NATIVE_UNIT_OF_MEASUREMENT: "°C",
                CONF_STATE_CLASS: "measurement",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SENSOR,
                CONF_NAME: "Temperature",
                CONF_KEY: "temperature",
                CONF_VALUE_TYPE: "number",
                CONF_INITIAL_VALUE: 21.5,
                CONF_NATIVE_UNIT_OF_MEASUREMENT: "°C",
                CONF_STATE_CLASS: "measurement",
            },
        ),
        (
            ENTITY_TYPE_BUTTON,
            {CONF_NAME: "Reset", CONF_KEY: ""},
            {CONF_ENTITY_TYPE: ENTITY_TYPE_BUTTON, CONF_NAME: "Reset", CONF_KEY: "reset"},
        ),
        (
            ENTITY_TYPE_LIGHT,
            {
                CONF_NAME: "Lamp",
                CONF_KEY: "",
                CONF_INITIAL_VALUE: True,
                CONF_BRIGHTNESS: 128,
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_LIGHT,
                CONF_NAME: "Lamp",
                CONF_KEY: "lamp",
                CONF_INITIAL_VALUE: True,
                CONF_BRIGHTNESS: 128,
            },
        ),
        (
            ENTITY_TYPE_NUMBER,
            {
                CONF_NAME: "Level",
                CONF_KEY: "",
                CONF_INITIAL_VALUE: 5,
                CONF_MIN: 0,
                CONF_MAX: 10,
                CONF_STEP: 1,
                CONF_MODE: "slider",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_NUMBER,
                CONF_NAME: "Level",
                CONF_KEY: "level",
                CONF_INITIAL_VALUE: 5.0,
                CONF_MIN: 0.0,
                CONF_MAX: 10.0,
                CONF_STEP: 1.0,
                CONF_MODE: "slider",
            },
        ),
        (
            ENTITY_TYPE_SELECT,
            {
                CONF_NAME: "Mode",
                CONF_KEY: "",
                CONF_OPTIONS: "auto, heat, cool",
                CONF_INITIAL_VALUE: "heat",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_SELECT,
                CONF_NAME: "Mode",
                CONF_KEY: "mode",
                CONF_OPTIONS: ["auto", "heat", "cool"],
                CONF_INITIAL_VALUE: "heat",
            },
        ),
        (
            ENTITY_TYPE_TEXT,
            {
                CONF_NAME: "Message",
                CONF_KEY: "",
                CONF_INITIAL_VALUE: "hello",
                CONF_MIN: 0,
                CONF_MAX: 20,
                CONF_MODE: "text",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_TEXT,
                CONF_NAME: "Message",
                CONF_KEY: "message",
                CONF_INITIAL_VALUE: "hello",
                CONF_MIN: 0,
                CONF_MAX: 20,
                CONF_MODE: "text",
            },
        ),
        (
            ENTITY_TYPE_DATE,
            {CONF_NAME: "Date", CONF_KEY: "", CONF_INITIAL_VALUE: "2026-04-25"},
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_DATE,
                CONF_NAME: "Date",
                CONF_KEY: "date",
                CONF_INITIAL_VALUE: "2026-04-25",
            },
        ),
        (
            ENTITY_TYPE_DATETIME,
            {
                CONF_NAME: "Date Time",
                CONF_KEY: "",
                CONF_INITIAL_VALUE: "2026-04-25T13:45:00+00:00",
            },
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_DATETIME,
                CONF_NAME: "Date Time",
                CONF_KEY: "date_time",
                CONF_INITIAL_VALUE: "2026-04-25T13:45:00+00:00",
            },
        ),
        (
            ENTITY_TYPE_TIME,
            {CONF_NAME: "Time", CONF_KEY: "", CONF_INITIAL_VALUE: "13:45:00"},
            {
                CONF_ENTITY_TYPE: ENTITY_TYPE_TIME,
                CONF_NAME: "Time",
                CONF_KEY: "time",
                CONF_INITIAL_VALUE: "13:45:00",
            },
        ),
    ],
)
async def test_config_flow_adds_entity_type(
    hass: HomeAssistant,
    entity_type: str,
    payload: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_NAME: "Test Device",
            CONF_DEVICE_ID: "virtual_device",
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_NONE,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ADD_ENTITY: True}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ENTITY_TYPE: entity_type}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=payload
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ADD_ENTITY: False}
    )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_ENTITIES] == [expected]
```

- [ ] **Step 2: Run config-flow tests and verify failure**

Run:

```bash
uv run pytest tests/test_config_flow.py -v
```

Expected: fails because the flow is switch-specific.

- [ ] **Step 3: Implement generic add flow**

In `config_flow.py`:

- replace `_switches` with `_entities`
- replace `async_step_switch_menu` with `async_step_entity_menu`
- add `async_step_add_entity_type`
- replace `async_step_add_switch` with `async_step_add_entity`
- create `_entity_schema(entity_type, defaults=None, include_key=True)`
- create `_entity_from_input(entity_type, user_input, key)`
- validate with shared model helpers

Keep type-specific schemas minimal:

- common fields: name, key, icon, entity_category, device_class
- switch/binary_sensor/light: boolean initial value
- sensor: value_type, initial_value, native_unit_of_measurement, state_class
- button: no initial value
- number: initial_value, min, max, step, unit, mode
- select: comma-separated options text, initial_value
- text: initial_value, min, max, mode
- date/time/datetime: initial_value

- [ ] **Step 4: Update strings**

Update labels from “switch” to “entity”, add `add_entity_type`, `add_entity`, and generic errors.

- [ ] **Step 5: Run config-flow tests**

Run:

```bash
uv run pytest tests/test_config_flow.py -v
```

Expected: all config-flow tests pass.

---

### Task 5: Options Flow Generic Add/Edit/Remove

**Files:**
- Modify: `custom_components/virtual/config_flow.py`
- Modify: `tests/test_config_flow.py`

- [ ] **Step 1: Update options-flow tests**

Replace switch-specific options tests with:

- add every supported entity type
- edit a sensor value/unit/state class
- edit a number min/max/step/current value
- edit a light brightness
- edit device metadata
- hard-remove multiple entities across different platforms

Ensure edit tests assert key and type remain unchanged.

- [ ] **Step 2: Run options tests and verify failure**

Run:

```bash
uv run pytest tests/test_config_flow.py -v
```

Expected: options tests fail because the flow still uses switch-specific actions and data.

- [ ] **Step 3: Implement generic options flow**

In `VirtualOptionsFlow`:

- rename actions to `add_entity`, `edit_entity`, `remove_entity`
- add type selection for add
- select existing entity by key for edit
- use `_entity_schema` for add/edit
- update `CONF_ENTITIES`
- hard-remove using `Platform(entity[CONF_ENTITY_TYPE])`, `DOMAIN`, and `entity_unique_id(device_id, key)`

- [ ] **Step 4: Run config-flow tests**

Run:

```bash
uv run pytest tests/test_config_flow.py -v
```

Expected: all config/options-flow tests pass.

---

### Task 6: Additional Platform Entity Classes

**Files:**
- Create: `custom_components/virtual/binary_sensor.py`
- Create: `custom_components/virtual/sensor.py`
- Create: `custom_components/virtual/button.py`
- Create: `custom_components/virtual/light.py`
- Create: `custom_components/virtual/number.py`
- Create: `custom_components/virtual/select.py`
- Create: `custom_components/virtual/text.py`
- Create: `custom_components/virtual/date.py`
- Create: `custom_components/virtual/datetime.py`
- Create: `custom_components/virtual/time.py`
- Modify: `custom_components/virtual/const.py`
- Create: `tests/test_platforms.py`

- [ ] **Step 1: Write failing platform setup tests**

Create one config entry containing all supported entity definitions. Assert after setup:

- each expected entity ID exists
- each entity registry entry has expected unique ID
- all entities share the virtual device
- initial states match configured values
- button has a state and exposes `last_pressed` only after press

- [ ] **Step 2: Run platform tests and verify failure**

Run:

```bash
uv run pytest tests/test_platforms.py -v
```

Expected: fails because platform files do not exist and `PLATFORMS` is not expanded.

- [ ] **Step 3: Expand `PLATFORMS`**

Update `const.py` with all platforms from the spec.

- [ ] **Step 4: Implement platform files**

Implement each file with:

```python
async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        VirtualX(entry.data, definition)
        for definition in entities_for_platform(entry.data, Platform.X)
    )
```

Use `RestoreEntity` for all stateful entity types.

Platform behavior:

- `binary_sensor`: `_attr_is_on`
- `sensor`: `_attr_native_value`, unit, state class
- `button`: `async_press`, `last_pressed` extra attribute
- `light`: `_attr_is_on`, `_attr_brightness`, `supported_color_modes={ColorMode.BRIGHTNESS}` when brightness configured, otherwise `{ColorMode.ONOFF}`
- `number`: `_attr_native_value`, min/max/step/unit/mode, `async_set_native_value`
- `select`: `_attr_options`, `_attr_current_option`, `async_select_option`
- `text`: `_attr_native_value`, min/max/mode, `async_set_value`
- `date`: `_attr_native_value`, `async_set_value`
- `time`: `_attr_native_value`, `async_set_value`
- `datetime`: `_attr_native_value`, `async_set_value`

- [ ] **Step 5: Run platform tests**

Run:

```bash
uv run pytest tests/test_platforms.py -v
```

Expected: all platform setup tests pass.

---

### Task 7: Native Services And Restore Behavior

**Files:**
- Modify: `tests/test_platforms.py`
- Modify platform files as needed

- [ ] **Step 1: Add failing tests for native services**

Test:

- switch turn on/off
- light turn on/off with brightness
- number set value
- select option
- text set value
- date set value
- time set value
- datetime set value
- button press updates `last_pressed`

- [ ] **Step 2: Add failing restore tests**

For each stateful platform, seed `homeassistant.helpers.restore_state.async_get(hass).last_states` and assert restored state wins over configured initial value.

- [ ] **Step 3: Run platform tests and verify failure**

Run:

```bash
uv run pytest tests/test_platforms.py -v
```

Expected: failures identify missing service or restore behavior.

- [ ] **Step 4: Implement missing native service and restore behavior**

Use the same pattern as current switch restore:

```python
if (last_state := await self.async_get_last_state()) is not None:
    self._restore_from_state(last_state)
```

Each platform should convert restored string state into its native type.

- [ ] **Step 5: Run platform tests**

Run:

```bash
uv run pytest tests/test_platforms.py -v
```

Expected: all platform tests pass.

---

### Task 8: `virtual.set_state` Service

**Files:**
- Modify: `custom_components/virtual/__init__.py`
- Modify: `custom_components/virtual/entity.py`
- Create: `custom_components/virtual/services.yaml`
- Create: `tests/test_set_state.py`

- [ ] **Step 1: Write failing service tests**

Create tests that:

- call `virtual.set_state` for binary sensor, sensor, switch, light, number, select, text, date, time, and datetime
- assert state updates
- call `virtual.set_state` for button and assert service validation failure
- call `virtual.set_state` with invalid number/select/date values and assert validation failure plus unchanged state

- [ ] **Step 2: Run service tests and verify failure**

Run:

```bash
uv run pytest tests/test_set_state.py -v
```

Expected: fails because service is not registered.

- [ ] **Step 3: Implement runtime entity registry**

In `entity.py`, add helpers that register/unregister virtual entities by entity ID or unique ID during entity lifecycle. Keep this registry under `hass.data[DOMAIN]["entities"]` or a `HassKey`.

Each stateful entity implements:

```python
async def async_set_virtual_state(self, value: Any) -> None:
    coerced = coerce_entity_value(self._definition, value)
    self._set_native_value(coerced)
    self.async_write_ha_state()
```

Button either does not implement it or raises `HomeAssistantError`.

- [ ] **Step 4: Register service**

In `__init__.py`, register `virtual.set_state` once in `async_setup`.

Service schema:

```python
vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.ensure_list,
        vol.Required(ATTR_VALUE): object,
    }
)
```

For this implementation, accept `entity_id` in service data rather than a target
selector. `services.yaml` must document `entity_id` and `value` as required
fields.

- [ ] **Step 5: Add `services.yaml`**

Define `set_state` with:

- required `entity_id` field
- required `value` field
- description that button is not supported

- [ ] **Step 6: Run service tests**

Run:

```bash
uv run pytest tests/test_set_state.py -v
```

Expected: all service tests pass.

---

### Task 9: Remove MVP Switch-Specific API Surface

**Files:**
- Modify: `custom_components/virtual/const.py`
- Modify: `custom_components/virtual/models.py`
- Modify all tests

- [ ] **Step 1: Remove compatibility aliases**

Remove:

- `CONF_SWITCHES`
- `generate_switch_key`
- `validate_unique_switch_key`
- `switch_unique_id`

Replace all remaining uses with:

- `CONF_ENTITIES`
- `generate_entity_key`
- `validate_unique_entity_key`
- `entity_unique_id`

- [ ] **Step 2: Run full tests and verify failures or pass**

Run:

```bash
uv run pytest tests/ -v
```

Expected: if any switch-specific references remain, tests fail with import/name errors.

- [ ] **Step 3: Fix remaining references**

Update code/tests until no switch-specific storage helpers remain.

- [ ] **Step 4: Run full tests**

Run:

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

---

### Task 10: Documentation And Final Verification

**Files:**
- Modify: `README.md`
- Modify: `custom_components/virtual/strings.json`
- Modify: `custom_components/virtual/translations/en.json`
- Modify: `custom_components/virtual/services.yaml`

- [ ] **Step 1: Update README**

Document:

- supported entity types
- minimal capabilities for each type
- config flow behavior
- options flow behavior
- `virtual.set_state` examples:

```yaml
service: virtual.set_state
target:
  entity_id: sensor.virtual_temperature
data:
  value: 21.5
```

```yaml
service: virtual.set_state
target:
  entity_id: binary_sensor.virtual_motion
data:
  value: true
```

- [ ] **Step 2: Run lint**

Run:

```bash
uv run ruff check custom_components/ tests/
```

Expected: `All checks passed!`

- [ ] **Step 3: Run format check**

Run:

```bash
uv run ruff format --check custom_components/ tests/
```

Expected: all files already formatted.

- [ ] **Step 4: Run full tests**

Run:

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add custom_components tests README.md docs/superpowers/plans/2026-04-25-virtual-entity-types.md
git commit -m "feat: add virtual entity type batch"
```

Expected: commit succeeds with clean worktree afterward.

---

## Execution Notes

- Commit after each task if the tests for that task pass cleanly.
- Do not add richer capabilities than the spec requires. In particular, skip full light color/effect support.
- Keep button excluded from `virtual.set_state`.
- Keep entity `key` and `type` immutable in options flow.
- If a Home Assistant platform service method name differs in `2026.4.3`, inspect the installed platform class and adapt to that version.
