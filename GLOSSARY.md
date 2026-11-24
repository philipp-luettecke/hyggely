# Glossary

Code, tests and docs use the **Term**. The UI shows the **German label**.

| Term | German label | Meaning |
|---|---|---|
| Room | Raum | A heated space. Owns one room climate entity, one or more TRVs, zero or more window contacts and exactly one schedule. |
| Room entity | Raum-Thermostat | The `climate` entity this integration creates per room. The only thermostat users see in HA, Apple Home and Google. |
| TRV | Heizkörperthermostat | A physical tado radiator thermostat, integrated locally via HomeKit Device as a `climate` entity. Never shown to users directly. |
| Schedule | Zeitplan | A native HA `schedule` helper assigned to one or more rooms. |
| Block | Block | One time range in a schedule. Carries a level in its additional data. |
| Block boundary | Schaltpunkt | Any moment where the effective level from the schedule changes (block start, block end, level change between adjacent blocks). |
| Level | Stufe | A named temperature tier. Schedule levels: `comfort`, `night`, `eco` (default outside blocks). Global levels: `away`, `vacation`, `frost`. Temperatures of schedule levels are set per room. |
| Lead time | Vorlaufzeit | Per-room duration by which a block's level is applied before the block starts, if it is warmer in the room than the level until then. |
| Room mode | Modus | The room entity's HVAC mode: `auto` (follow schedule), `heat` (override active), `off` (frost protection). |
| Override | Manuelle Übersteuerung | A setpoint chosen by a person (knob, Siri, Google, HA app, panel). Puts the room into `heat` until it expires. |
| External change | Externe Änderung | A TRV state change not caused by this integration, e.g. a knob turn. Detected, then turned into an override. |
| Echo | Echo | The immediate TRV state update (< 0.2 s) that reflects a command this integration sent. tado sends no later echoes. Must not become an override. |
| Unreachable | Nicht erreichbar | A TRV whose `climate` entity or the temperature sensor of its device is `unavailable`. On a bridge outage the `climate` entity only freezes (ticket 01). Gets no commands. |
| Offline | Offline | A TRV unreachable for longer than 30 min. Shown under repairs. |
| Override expiry | Rückfall | When a room returns to `auto`. Policy per room: `next_block`, `duration`, or `earliest` (default, 3 h). `off` always returns at the next block boundary. |
| House mode | Hausbetriebsart | Global mode: `auto`, `vacation` (with end time), `off`. |
| Away | Abwesend | Derived state: all configured persons not home for the presence delay. Not a house mode. |
| Presence delay | Abwesenheitsverzögerung | Global duration all configured persons must be not home before Away applies (default 30 min). |
| Window open | Fenster offen | Any window contact of a room open for longer than the window delay. |
| Reason | Grund | Human-readable explanation of a room's current target, e.g. "Fenster offen seit 14:03". |
| Target resolver | — | Pure decision logic: given a room's inputs, returns target, room mode to send and reason. |
| Heating panel | Heizung (Seitenleiste) | Sidebar panel of this integration for overview, schedules, levels and house mode. Admin-only. |
