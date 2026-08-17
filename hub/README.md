# Alpilab Hub

Conceptual Windows PC bridge between ALPILAB AI Cloud and lab hardware/software.

## Status

Phase 1 provides **interfaces and mocks only** (`hub/alpilab_hub.py`).

## Planned capabilities

- `open_application` / `close_application` (permission + confirmation required)
- `capture_microscope`
- `capture_thermal_camera`
- `read_multimeter`
- `read_power_supply`
- `get_pc_status`

## Hard rules

- No arbitrary shell / remote shell
- No execution of user-supplied commands
- Dangerous actions require permissions and explicit confirmation
- Real Windows process/hardware control is **not** implemented yet
