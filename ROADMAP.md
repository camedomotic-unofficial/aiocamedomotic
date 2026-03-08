<!-- Copyright 2024 - GitHub user: fredericks1982

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.  -->

# Development roadmap

## Introduction

This document outlines the planned development path for this library. The roadmap
reflects our commitment to making home automation more accessible and manageable.

This roadmap is subject to change based on community feedback and ongoing development
insights. We look forward to growing this library together with our users and contributors.

## Current Features (Version 1.4)

- **Session management**: Automated handling of login, logout, and keep-alive processes
  for the API, with automatic session recovery.
- **Lights management**: List and control lights (on/off, dimmer brightness, RGB color).
- **Openings management**: List and control shutters/blinds (open, close, stop).
- **Scenarios management**: List available scenarios and trigger their activation.
- **Thermoregulation (read-only)**: List thermoregulation zones with their current state,
  retrieve temperature, setpoint, mode, and season for each zone. Expose top-level analog
  sensor readings (temperature, humidity, pressure) from the thermo response.
- **Real-time updates with typed classes**: Long-polling support with typed update objects
  (`LightUpdate`, `OpeningUpdate`, `ThermoZoneUpdate`, `ScenarioUpdate`,
  `DigitalInputUpdate`, `PlantUpdate`). `UpdateList` provides filtering by device type,
  typed access via `get_typed_updates()` and `get_typed_by_device_type()`, and a
  `has_plant_update` property for detecting plant configuration changes. Unrecognized
  indications fall back to a generic `DeviceUpdate`.
- **Configurable command timeout**: Instance-level `command_timeout` parameter (default
  30 seconds) applies to all commands, with per-call `timeout` override on
  `async_get_updates()` for long-polling scenarios.
- **Discovery**: Server info, feature detection, user listing, floor and room topology.

## Planned Features

All planned features below are backed by real traffic captures from a domestic CAME
Domotic plant and can be tested against a real server. Features that are only known from
reverse-engineered sources (without real traffic verification) are listed separately
under [Future considerations](#future-considerations).

### Version 1.5 — Energy meters

- **Meter listing**: List all energy meters with their current readings.
- **Instant power**: Expose real-time power consumption via `meter_instant_power_ind`.
- **Energy statistics**: Query historical consumption data (`energy_stat_req`) for
  monitoring and dashboard integration.

### Version 1.6 — Load control (read-only)

- **Load control meters**: List load control meters with their current state
  (`loadsctrl_meter_list_req`).
- **Load control relays**: List load control relays with their current priorities
  (`loadsctrl_relay_list_req`).
- **Status indications**: Handle `loadsctrl_meter_ind` and `loadsctrl_relay_ind` for
  real-time load state updates.

## Future considerations

The following features are known from reverse-engineered sources (API_reference.md,
API_MANUAL.md) but have not been verified with real traffic captures. They may be
considered for future development once real-world testing is possible:

- **Thermoregulation (control)**: Set target temperature for individual thermo zones,
  switch between heating and cooling seasons (`thermo_season_req`), configure operating
  mode, fan speed, and dehumidification, and get/set thermoregulation profiles with
  extended info support.
- **Load control (edit)**: Configure load control meter thresholds
  (`loadsctrl_meter_set_req`) and load control relay priorities
  (`loadsctrl_relay_set_req`).

- **Relays (generic switches)**: List and control generic relay actuators. The API is
  documented but no real traffic has been observed.
- **Digital inputs**: List binary sensors (door contacts, motion sensors, etc.) via
  `digitalin_list_req`. Update parsing is already implemented (`DigitalInputUpdate`),
  but a device model class and list command are not yet available.
- **User management**: Add, delete, and change passwords for users on the CAME server.
- **Scenario management**: Create and delete scenarios (beyond the current list/activate).
- **Audio system**: Sound zone and source management (entirely unverified).
- **Cameras (TVCC)**: Camera listing (entirely unverified).
- **Security system**: Area/scenario management and alarm control (entirely unverified).
- **Maps**: Floor plan/map retrieval (entirely unverified).
- **Status updates management**: Automatic long-polling loop with event callbacks,
  push-based state synchronization, and automatic `plant_update_ind` handling for full
  cache invalidation. Typed update classes and filtering are already available (v1.4);
  this item covers the higher-level automation layer on top.
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
