<!-- SPDX-FileCopyrightText: 2026 - GitHub user: fredericks1982
SPDX-License-Identifier: Apache-2.0 -->

# Development roadmap

## Introduction

This document outlines the planned development path for this library. The roadmap
reflects our commitment to making home automation more accessible and manageable.

This roadmap is subject to change based on community feedback and ongoing development
insights. We look forward to growing this library together with our users and contributors.

## Current Features (Version 1.13)

- **Session management**: Automated handling of login, logout, and keep-alive processes
  for the API, with automatic session recovery.
- **Lights management**: List and control lights (on/off, dimmer brightness, RGB color).
- **Openings management**: List and control shutters/blinds (open, close, stop, slat
  tilting).
- **Scenarios management**: List available scenarios and trigger their activation, either
  by scenario object or directly by name (`scenario_activation_by_name_req`) without
  fetching the list first. Creating and deleting scenarios remains under
  [Future considerations](#future-considerations), pending a real capture of the
  registration flow.
- **Thermoregulation (full control)**: List thermoregulation zones with their current
  state; set target temperature, operating mode (OFF, MANUAL, AUTO, JOLLY), and fan speed
  (OFF, SLOW, MEDIUM, FAST, AUTO) for individual zones via `thermo_zone_config_req`.
  Switch between seasons (WINTER, SUMMER, PLANT_OFF) plant-wide via `thermo_season_req`.
  Expose fan speed, dehumidifier state (enabled/setpoint), and auxiliary temperature
  sensors (t1, t2, t3) on `ThermoZone` and `ThermoZoneUpdate`. Top-level analog sensor
  readings (temperature, humidity, pressure) are also exposed. Each zone's weekly
  setpoint schedule (8 rows: Monday–Sunday plus the JOLLY profile, quarter-hour wire
  resolution) is exposed **read-only** as a typed, immutable `ThermoProfile` object.
- **Timers management**: List timers with their timetables via `timers_list_req`;
  enable/disable timers, toggle individual days, and set timetables via
  `timers_enable_req`, `timers_enable_day_req`, and `timers_set_req`.
- **Energy meters (read-only)**: List energy meters with their instant power readings
  and cumulative energy counters via `meters_list_req`; real-time readings via
  `meter_instant_power_ind`.
- **Load control (full)**: List load control meters and their managed loads
  (`loadsctrl_meter_list_req`, `loadsctrl_relay_list_req`); enable/disable individual
  loads, change their detach priorities (including bulk reordering), and configure the
  controller's power threshold and hysteresis (`loadsctrl_relay_set_req`,
  `loadsctrl_meter_set_req`); real-time state via `loadsctrl_meter_ind` and
  `loadsctrl_relay_ind`. The controller's weekly threshold profile (`profile_data`:
  7 days × 24 hourly levels, each level 1–5 selecting the active threshold as a
  fraction of `max_power`) can be read, edited, and written back through the typed,
  immutable `LoadsCtrlProfile` API (verified against a real plant).
- **Generic relays**: List and control simple on/off relay actuators via
  `relays_list_req` and `relay_activation_req`, either by relay object or directly by
  name. Timed activation (switch on for a fixed interval, then auto-off) is available via
  `relay_timed_req`; the interval unit is undocumented (likely seconds) and not yet
  verified against a real server.
- **Digital inputs**: List binary sensors (door contacts, motion sensors, etc.)
  via `digitalin_list_req`. Each digital input exposes its current state and attributes.
  Real-time updates are supported via `DigitalInputUpdate`. Inputs that latch a technical
  alarm or signalling counter can be acknowledged via `digitalin_ack_req`.
- **Analog inputs (read-only)**: List standalone analog sensors (hygrometers,
  thermometers, barometers) via `analogin_list_req`, independent of the
  thermoregulation sensors.
- **Cameras (TVCC, read-only)**: List IP cameras with their stream URIs.
- **Maps (read-only)**: Retrieve floor-plan map pages with positioned device elements
  via `map_descr_req`.
- **User management**: Create and remove users on the CAME server, update passwords,
  and list terminal permission groups.
- **Real-time updates with typed classes**: Long-polling support with typed update objects
  (`LightUpdate`, `OpeningUpdate`, `ThermoZoneUpdate`, `ScenarioUpdate`, `RelayUpdate`,
  `DigitalInputUpdate`, `AnalogInUpdate`, `TimerUpdate`, `EnergyMeterUpdate`,
  `LoadsCtrlMeterUpdate`, `LoadsCtrlRelayUpdate`, `PlantUpdate`). `UpdateList` provides
  filtering by device type, typed access via `get_typed_updates()` and
  `get_typed_by_device_type()`, and a `has_plant_update` property for detecting plant
  configuration changes. Unrecognized indications fall back to a generic `DeviceUpdate`.
- **Configurable command timeout**: Instance-level `command_timeout` parameter (default
  30 seconds) applies to all commands, with per-call `timeout` override on
  `async_get_updates()` for long-polling scenarios.
- **Discovery**: Server info, feature detection, user listing, merged floor and room
  topology, and a connectivity check with latency measurement (`async_ping`).

## Planned Features

Features that are only known from reverse-engineered sources (without real traffic
verification) are listed separately under
[Future considerations](#future-considerations).

### Version 1.14 — Thermostat profile writing

- **Weekly schedule editing**: Write the thermostat zones' weekly setpoint profiles
  back to the server, enabling AUTO-mode weekly programming from the library. Reading
  and editing are already supported through the typed `ThermoProfile` API; writing is
  blocked on capturing the profile set command from the official app, which has not
  been observed in real traffic yet.

## Future considerations

The following features are known from reverse-engineered sources (API_reference.md,
API_MANUAL.md) but have not been verified with real traffic captures. They may be
considered for future development once real-world testing is possible:

- **Scenario management**: Create and delete scenarios (beyond the current
  list/activate/activate-by-name).
- **Energy statistics**: Historical energy statistics per meter (`energy_stat_req`) and
  plant-wide measurement history reset (`energy_reset_store_req`) — deferred until real traffic captures are available.
- **Audio system**: Sound zone and source management (entirely unverified).
- **Security system**: Area/scenario management and alarm control (entirely unverified).
- **Infrastructure improvements**: Automated keep-alive scheduling, per-actuator scope
  queries, and connection resilience improvements.

## Contributing

We welcome contributions from the community, whether it's in the form of feature
requests, bug reports, or pull requests. For more information on how to contribute,
please see our [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Feedback

Your feedback is invaluable to us. It helps in shaping the roadmap and ensuring that
we are meeting the needs of our users. Please feel free to submit issues or suggestions
through our GitHub repository.
