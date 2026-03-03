# CAME ETI/Domo API — Comprehensive Documentation

## Context

This document fully describes the CAME ETI/Domo HTTP API as reverse-engineered from the existing `pycame` wrapper in `custom_components/came/pycame/`. The goal is to provide everything needed to write a new, clean API wrapper from scratch.

---

## 1. Transport Layer

### 1.1 Connection Details

| Property | Value |
|----------|-------|
| **Base URL** | `http://{host}/domo/` |
| **HTTP Method** | `POST` (all requests) |
| **Content-Type** | `application/x-www-form-urlencoded` |
| **Body encoding** | `command=<JSON string>` |
| **Response format** | JSON |

### 1.2 Request Headers

```
User-Agent: PythonCameManager/{VERSION}
Accept: application/json, text/plain, */*
Content-Type: application/x-www-form-urlencoded
Authorization: access_token {TOKEN}
```

The `TOKEN` is a pre-existing access token provided at configuration time (not obtained via login — it is required before any API call).

### 1.3 Raw HTTP Example

```http
POST /domo/ HTTP/1.1
Host: 192.168.1.100
Content-Type: application/x-www-form-urlencoded
Authorization: access_token mytoken123

command={"sl_cmd":"sl_registration_req","sl_login":"user","sl_pwd":"pass"}
```

---

## 2. Protocol Layers

The API uses a **two-layer protocol**:

### 2.1 Session Layer (`sl_*`)

All requests are wrapped in a session-layer envelope.

**Login request:**
```json
{
  "sl_cmd": "sl_registration_req",
  "sl_login": "<username>",
  "sl_pwd": "<password>"
}
```

**Application-layer request (after login):**
```json
{
  "sl_cmd": "sl_data_req",
  "sl_client_id": "<client_id>",
  "sl_appl_msg": { /* application command */ }
}
```

**All responses** include:
```json
{
  "sl_data_ack_reason": 0,
  "sl_cmd": "<response_command>"
}
```

### 2.2 Application Layer (`cmd_name`)

Nested inside `sl_appl_msg`. Each command has a `cmd_name` field. Responses contain the application-layer fields at top level (alongside the session-layer fields).

---

## 3. Authentication & Session Management

### 3.1 Login

| Field | Value |
|-------|-------|
| **Request `sl_cmd`** | `sl_registration_req` |
| **Response `sl_cmd`** | `sl_registration_ack` |

**Request:**
```json
{
  "sl_cmd": "sl_registration_req",
  "sl_login": "<username>",
  "sl_pwd": "<password>"
}
```

**Response (success):**
```json
{
  "sl_cmd": "sl_registration_ack",
  "sl_client_id": "<session_id>",
  "sl_data_ack_reason": 0
}
```

The returned `sl_client_id` must be included in every subsequent `sl_data_req`.

### 3.2 Session Lifecycle

- `sl_client_id` is set upon successful login
- On any connection error, the client should clear `sl_client_id` and re-login on the next request
- The wrapper auto-logs-in before every `application_request` if not already logged in

---

## 4. Error Codes

The field `sl_data_ack_reason` appears in every response:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid user |
| 3 | Too many sessions during login |
| 4 | Error in JSON syntax |
| 5 | No session layer command tag |
| 6 | Unrecognized session layer command |
| 7 | No client ID in request |
| 8 | Wrong client ID in request |
| 9 | Wrong application command |
| 10 | No reply to application command (service may be down) |
| 11 | Wrong application data |

---

## 5. Discovery Commands

### 5.1 Feature List

Returns which device categories the ETI/Domo supports plus device metadata.

**Request:**
```json
{ "cmd_name": "feature_list_req" }
```

**Response (`feature_list_resp`):**
```json
{
  "cmd_name": "feature_list_resp",
  "swver": "<software_version>",
  "serial": "<serial_number>",
  "keycode": "<keycode>",
  "list": ["lights", "openings", "thermoregulation", "energy", "digitalin", "scenarios", "relays"]
}
```

**Known feature strings:** `lights`, `openings`, `relays`, `thermoregulation`, `energy`, `digitalin`, `scenarios`

### 5.2 Floor List

**Request:**
```json
{
  "cmd_name": "floor_list_req",
  "topologic_scope": "plant"
}
```

**Response (`floor_list_resp`):**
```json
{
  "cmd_name": "floor_list_resp",
  "floor_list": [
    { "floor_ind": 0, "name": "Ground Floor" }
  ]
}
```

### 5.3 Room List

**Request:**
```json
{
  "cmd_name": "room_list_req",
  "topologic_scope": "plant"
}
```

**Response (`room_list_resp`):**
```json
{
  "cmd_name": "room_list_resp",
  "room_list": [
    { "room_ind": 0, "name": "Living Room", "floor_ind": 0 }
  ]
}
```

---

## 6. Device List Commands

All device list commands use `"topologic_scope": "plant"` to retrieve all devices, or `"topologic_scope": "act"` with `"value": <act_id>` to get a single device.

### 6.1 Lights

**Request:** `light_list_req` / **Response:** `light_list_resp`

```json
{ "cmd_name": "light_list_req", "topologic_scope": "plant" }
```

**Response item fields:**

| Field | Type | Description |
|-------|------|-------------|
| `act_id` | int | Unique actuator ID |
| `name` | str | Device name |
| `type` | str | `"STEP_STEP"`, `"DIMMER"`, or `"RGB"` |
| `status` | int | `0`=OFF, `1`=ON, `4`=AUTO |
| `perc` | int | Brightness 0-100 (for DIMMER/RGB) |
| `rgb` | [int,int,int] | RGB values 0-255 each (for RGB type) |
| `floor_ind` | int | Floor index |
| `room_ind` | int | Room index |

**Light types:**

| Type | Supports Brightness | Supports Color |
|------|--------------------:|---------------:|
| `STEP_STEP` | No | No |
| `DIMMER` | Yes (0-100%) | No |
| `RGB` | Yes (via HSV V channel) | Yes (RGB) |

**Light states:** `0`=OFF, `1`=ON, `4`=AUTO

### 6.2 Openings (Covers/Blinds)

**Request:** `openings_list_req` / **Response:** `openings_list_resp`

```json
{ "cmd_name": "openings_list_req", "topologic_scope": "plant" }
```

**Response item fields:**

| Field | Type | Description |
|-------|------|-------------|
| `open_act_id` | int | Actuator ID (**note: different key from other devices**) |
| `name` | str | Device name |
| `status` | int | `0`=STOP, `1`=OPEN, `2`=CLOSE |
| `floor_ind` | int | Floor index |
| `room_ind` | int | Room index |

**Opening states:** `0`=STOP, `1`=OPEN, `2`=CLOSE (also `3`=slat open, `4`=slat close — referenced in comments but not implemented)

### 6.3 Relays (Generic Switches)

**Request:** `relays_list_req` / **Response:** `relays_list_resp`

```json
{ "cmd_name": "relays_list_req", "topologic_scope": "plant" }
```

**Response item fields:**

| Field | Type | Description |
|-------|------|-------------|
| `act_id` | int | Actuator ID |
| `name` | str | Device name |
| `status` | int | `0`=OFF, `1`=ON |
| `floor_ind` | int | Floor index |
| `room_ind` | int | Room index |

### 6.4 Thermostats (Thermoregulation)

**Request:** `thermo_list_req` / **Response:** `thermo_list_resp`

```json
{ "cmd_name": "thermo_list_req", "topologic_scope": "plant" }
```

**Response item fields (in `array`):**

| Field | Type | Description |
|-------|------|-------------|
| `act_id` | int | Actuator ID |
| `name` | str | Device name |
| `status` | int | `0`=OFF, `1`=ON |
| `mode` | int | `0`=OFF, `1`=MANUAL, `2`=AUTO, `3`=JOLLY |
| `season` | str | `"plant_off"`, `"winter"`, `"summer"` |
| `temp` | int | Current temperature × 10 (e.g. 215 = 21.5°C) |
| `temp_dec` | int | Alternative field for current temperature × 10 |
| `set_point` | int | Target temperature × 10 |
| `fan_speed` | int | `0`=OFF, `1`=SLOW, `2`=MEDIUM, `3`=FAST, `4`=AUTO |
| `dehumidifier` | object | `{ "enabled": 0\|1, "setpoint": <humidity%> }` |
| `t1` | int\|null | Temperature sensor 1 |
| `t2` | int\|null | Temperature sensor 2 |
| `t3` | int\|null | Temperature sensor 3 |
| `antifreeze` | int | Antifreeze setting |
| `reason` | int | Mode reason code |
| `f3a` | object | Advanced settings |
| `thermo_algo` | object | Algorithm settings |
| `floor_ind` | int | Floor index |
| `room_ind` | int | Room index |

**Additionally**, the thermo_list_resp contains **analog sensors** as top-level fields (not in the `array`):

```json
{
  "cmd_name": "thermo_list_resp",
  "array": [ /* thermostat zones */ ],
  "temperature": { "name": "...", "value": 215, "unit": "°C", "act_id": ... },
  "humidity":    { "name": "...", "value": 55,  "unit": "%",  "act_id": ... },
  "pressure":    { "name": "...", "value": 1013, "unit": "hPa", "act_id": ... }
}
```

**Thermostat modes:** `0`=OFF, `1`=MANUAL, `2`=AUTO, `3`=JOLLY

**Seasons:** `"plant_off"`, `"winter"`, `"summer"`

**Fan speeds:** `0`=OFF, `1`=SLOW, `2`=MEDIUM, `3`=FAST, `4`=AUTO

**Dehumidifier states:** `0`=OFF, `1`=ON

### 6.5 Energy Meters

**Request:** `meters_list_req` / **Response:** `meters_list_resp`

```json
{ "cmd_name": "meters_list_req", "topologic_scope": "plant" }
```

**Response item fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Meter identifier (used for matching in push updates) |
| `act_id` | int\|null | Actuator ID (may be absent — these are "unmanaged") |
| `name` | str | Device name |
| `instant_power` | float | Current power in Watts |
| `produced` | float | Total energy produced |
| `last_24h_avg` | float | 24-hour average power |
| `last_month_avg` | float | Monthly average power |
| `unit` | str | Power unit (default "W") |
| `energy_unit` | str | Energy unit (e.g. "kWh") |
| `floor_ind` | int | Floor index |
| `room_ind` | int | Room index |

### 6.6 Digital Inputs (Binary Sensors)

**Request:** `digitalin_list_req` / **Response:** `digitalin_list_resp`

```json
{ "cmd_name": "digitalin_list_req", "topologic_scope": "plant" }
```

**Response item fields:**

| Field | Type | Description |
|-------|------|-------------|
| `act_id` | int | Actuator ID |
| `name` | str | Device name |
| `status` | int | `0`=OFF, `1`=ON |
| `floor_ind` | int | Floor index |
| `room_ind` | int | Room index |

### 6.7 Scenarios

**Request:** `scenarios_list_req` / **Response:** `scenarios_list_resp`

```json
{ "cmd_name": "scenarios_list_req" }
```

Note: No `topologic_scope` needed.

**Response item fields (in `array`):**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Scenario identifier |
| `name` | str | Scenario name |

---

## 7. Control Commands

All control commands return `generic_reply` unless noted:

```json
{ "cmd_name": "generic_reply", "sl_data_ack_reason": 0 }
```

### 7.1 Light Switch

```json
{
  "cmd_name": "light_switch_req",
  "act_id": <int>,
  "wanted_status": <0|1|4>,
  "perc": <0-100>,
  "rgb": [<R>, <G>, <B>]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `act_id` | Yes | Target light |
| `wanted_status` | Yes | `0`=OFF, `1`=ON, `4`=AUTO |
| `perc` | No | Brightness 0-100 (DIMMER/RGB) |
| `rgb` | No | RGB color [0-255, 0-255, 0-255] (RGB type only) |

### 7.2 Opening Move

```json
{
  "cmd_name": "opening_move_req",
  "act_id": <int>,
  "wanted_status": <0|1|2>
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `act_id` | Yes | Target opening (uses `open_act_id` from device info) |
| `wanted_status` | Yes | `0`=STOP, `1`=OPEN, `2`=CLOSE |

### 7.3 Relay Activation

```json
{
  "cmd_name": "relay_activation_req",
  "act_id": <int>,
  "wanted_status": <0|1>
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `act_id` | Yes | Target relay |
| `wanted_status` | Yes | `0`=OFF, `1`=ON |

### 7.4 Thermostat Zone Config

```json
{
  "cmd_name": "thermo_zone_config_req",
  "act_id": <int>,
  "mode": <0|1|2|3>,
  "set_point": <int>,
  "extended_infos": <0|1>,
  "season": "<string>",
  "fan_speed": <0|1|2|3|4>
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `act_id` | Yes | Target thermostat zone |
| `mode` | Yes | `0`=OFF, `1`=MANUAL, `2`=AUTO, `3`=JOLLY (falls back to current if not changing) |
| `set_point` | Yes | Target temperature × 10 (falls back to current if not changing) |
| `extended_infos` | Yes | Set to `1` if `season` or `fan_speed` is included, else `0` |
| `season` | No | `"plant_off"`, `"winter"`, `"summer"` |
| `fan_speed` | No | `0`=OFF, `1`=SLOW, `2`=MEDIUM, `3`=FAST, `4`=AUTO |

### 7.5 Scenario Activation

```json
{
  "cmd_name": "scenario_activation_req",
  "id": <int>
}
```

**Note:** The expected response may be `generic_reply` but the actual response name can differ. The existing wrapper sets `resp_command=None` and catches mismatches.

### 7.6 Scenario Creation

```json
{
  "cmd_name": "scenario_registration_start",
  "name": "<scenario_name>"
}
```

**Response:** `scenario_registration_start_ack`

### 7.7 Scenario Deletion

```json
{
  "cmd_name": "scenario_delete_req",
  "id": <int>
}
```

**Response:** `scenario_delete_resp`

---

## 8. Status Update (Long Polling)

The primary mechanism for real-time state changes.

**Request:**
```json
{
  "cmd_name": "status_update_req",
  "timeout": <seconds>
}
```

The `timeout` field is optional.

**Response (`status_update_resp`):**
```json
{
  "cmd_name": "status_update_resp",
  "result": [
    { "cmd_name": "<update_type>", "act_id": <int>, ...fields... },
    ...
  ]
}
```

### 8.1 Update Indication Types

The `cmd_name` within each result item indicates what changed:

| cmd_name | Meaning |
|----------|---------|
| `light_update_ind` | Light state changed |
| `opening_update_ind` | Opening state changed |
| `relay_update_ind` | Relay state changed |
| `thermo_update_ind` | Thermostat state changed |
| `digitalin_update_ind` | Digital input state changed |
| `plant_update_ind` | Plant configuration changed (full device refresh needed) |
| `scenario_status_ind` | Scenario status changed (has `id` field) |
| `scenario_user_ind` | User scenario action (`action` field: `"add"`, `"create"`) |

Each update indication contains the same fields as the corresponding device in the list response, keyed by `act_id` for matching.

When `plant_update_ind` is received, all cached devices should be discarded and re-fetched.

---

## 9. Single-Device Force Update

To refresh a single device, use the list command with per-actuator scope:

```json
{
  "cmd_name": "<type>_list_req",
  "topologic_scope": "act",
  "value": <act_id>
}
```

Where `<type>` is: `light`, `opening`, `relay`, `thermo`, `meters`, `digitalin`.

The response uses the corresponding `<type>_list_resp` with the same field structure.

**Note:** For some types (e.g. analog sensors returned under `thermo`), the response field may not be `"array"` but a named field like `"temperature"`, `"humidity"`, or `"pressure"`.

---

## 10. Device Type Registry

These are all known device types in the ETI/Domo system:

| Type ID | Name | Implemented | API Feature |
|---------|------|:-----------:|-------------|
| -2 | Energy Sensor | Yes | `energy` |
| -1 | Analog Sensor | Yes | (embedded in `thermoregulation`) |
| 0 | Light | Yes | `lights` |
| 1 | Opening | Yes | `openings` |
| 2 | Thermostat | Yes | `thermoregulation` |
| 3 | Page | No | — |
| 4 | Scenario | Yes | `scenarios` |
| 5 | Camera | No | — |
| 6 | Security Panel | No | — |
| 7 | Security Area | No | — |
| 8 | Security Scenario | No | — |
| 9 | Security Input | No | — |
| 10 | Security Output | No | — |
| 11 | Generic Relay | Yes | `relays` |
| 12 | Generic Text | No (disabled) | — |
| 13 | Sound Zone | No | — |
| 14 | Digital Input | Yes | `digitalin` |

---

## 11. Complete API Endpoint Summary

| # | Request `cmd_name` | Response `cmd_name` | `topologic_scope` | Key Response Fields |
|---|-------------------|---------------------|-------------------|---------------------|
| 1 | `feature_list_req` | `feature_list_resp` | — | `swver`, `serial`, `keycode`, `list` |
| 2 | `floor_list_req` | `floor_list_resp` | `plant` | `floor_list` |
| 3 | `room_list_req` | `room_list_resp` | `plant` | `room_list` |
| 4 | `light_list_req` | `light_list_resp` | `plant` or `act` | `array` |
| 5 | `openings_list_req` | `openings_list_resp` | `plant` or `act` | `array` |
| 6 | `relays_list_req` | `relays_list_resp` | `plant` or `act` | `array` |
| 7 | `thermo_list_req` | `thermo_list_resp` | `plant` or `act` | `array`, `temperature`, `humidity`, `pressure` |
| 8 | `meters_list_req` | `meters_list_resp` | `plant` or `act` | `array` |
| 9 | `digitalin_list_req` | `digitalin_list_resp` | `plant` or `act` | `array` |
| 10 | `scenarios_list_req` | `scenarios_list_resp` | — | `array` |
| 11 | `light_switch_req` | `generic_reply` | — | — |
| 12 | `opening_move_req` | `generic_reply` | — | — |
| 13 | `relay_activation_req` | `generic_reply` | — | — |
| 14 | `thermo_zone_config_req` | `generic_reply` | — | — |
| 15 | `scenario_activation_req` | *(varies)* | — | — |
| 16 | `scenario_registration_start` | `scenario_registration_start_ack` | — | — |
| 17 | `scenario_delete_req` | `scenario_delete_resp` | — | — |
| 18 | `status_update_req` | `status_update_resp` | — | `result` (array of update indications) |

---

## 12. Known Quirks & Edge Cases

1. **Opening uses `open_act_id`** instead of `act_id` — the only device type that does this.
2. **Energy sensors may lack `act_id`** — they use `id` for matching in push updates and may raise "unmanaged device" errors on force-update.
3. **Thermostat temperatures are × 10** — `set_point=215` means 21.5°C.
4. **Analog sensors are nested** in the `thermo_list_resp` as top-level fields (`temperature`, `humidity`, `pressure`), not in the `array`.
5. **Scenario activation response** doesn't always match `generic_reply` — the wrapper catches this mismatch specially.
6. **`plant_update_ind`** in status updates means the entire device topology changed and all caches must be invalidated.
7. **`extended_infos`** flag in thermostat config must be set to `1` when sending `season` or `fan_speed`.
8. **Digital input** references `self._update_cmd_base` and `self._update_src_field` which are never initialized in its `__init__` — this is a bug in the current wrapper.
9. **Fan speed `0` (OFF)** is treated as AUTO in the HA mapping — when the fan is OFF, the app shows it as AUTO.
10. **`status_update_req`** blocks (long polls) until a state change occurs or the optional timeout expires.
