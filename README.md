# Climate Control

Home Assistant custom integration for smart, family-friendly heating control: one room thermostat per room that follows a native schedule helper, respects manual overrides and reacts to open windows, presence and vacation.

- One **room thermostat** (`climate` entity) per room with the modes `auto` (follow the schedule), `heat` (manual override until it expires) and `off` (frost protection until the next block boundary). It is the only thermostat people need to see, in Home Assistant, Apple Home and Google Home.
- Schedules are native `schedule` helpers. Each block carries a level (comfort or night); outside the blocks eco applies. The temperature of every level is set per room.
- A turn of the knob, Siri, Google or the app becomes a manual override and falls back to the schedule by itself.
- Open windows, away, vacation and the house mode apply automatically. A reason sensor explains every target in plain text.
- The sidebar panel "Heizung" ("Heating") shows all rooms and edits schedules, levels, lead times and the house mode. It is for admins only.

The integration was built for tado radiator thermostats (TRVs) connected locally through the [HomeKit Device](https://www.home-assistant.io/integrations/homekit_controller/) integration, but it drives any `climate` entity that offers the HVAC modes `heat` and `off`.

## Requirements

- Home Assistant 2026.11 or newer.
- One or more TRVs per room as `climate` entities with the modes `heat` and `off`. Targets are limited to 5–25 °C in steps of 1 °C.
- An admin account for everyone who edits schedules: the panel and the native schedule commands are admin-only.
- Optional: window contacts (`binary_sensor`), persons (`person`) for away, and `notify` entities (for example the Companion App on your phones) for notifications.

## Installation

### HACS

1. In HACS, open the menu in the top right corner and choose **Custom repositories**.
2. Enter the URL of this repository and choose the type **Integration**.
3. Search for **Climate Control**, download it and restart Home Assistant.

Updates show up in HACS. Restart Home Assistant after each update.

### Manual

1. Download the latest release (or the repository) and copy the folder `custom_components/climate_control` into the `custom_components` folder of your Home Assistant configuration, so that `config/custom_components/climate_control/manifest.json` exists.
2. Restart Home Assistant.

The panel is part of the integration folder (`frontend/heating-panel.js`); there is nothing to build.

## Setup

### Main entry

Go to **Settings → Devices & services → Add integration** and choose **Climate Control**. The dialog asks for the global settings that apply to all rooms. The integration can be added only once.

| Setting | Default | Meaning |
|---|---|---|
| Persons | none | The house is away when all of these persons are not home. |
| Presence delay | 30 min | How long all persons must be gone before away applies. |
| Notification recipients | none | `notify` entities that get the messages. |
| Quiet time | 22:00–07:00 | No messages in this time; what still applies is sent at its end. |
| Away, vacation, frost protection temperature | 17 °C, 15 °C, 7 °C | Targets while away, during a vacation, and while a window is open, a room is off or the house is off. |
| Override expiry | earlier of next block boundary and 3 h | When a manual override returns to the schedule. Rooms can deviate. |
| Window delay | 60 s | How long a window must be open before the room switches to frost protection. |

Change them later with **Configure** on the integration entry. The panel also changes the three global temperatures.

### Rooms

Each room is a sub-entry of the main entry. On the integration entry choose **Add room** ("Raum hinzufügen"):

- **Name** and **Area**: the room appears as a device in this area, with its room thermostat and its reason sensor.
- **Radiator thermostats**: one or more TRVs. All of them get the same target; the current temperature is the mean of the reachable ones. A turn of the knob on any of them overrides the whole room.
- **Window contacts** (optional): while one of them is open for longer than the window delay, the room gets frost protection. An unreachable contact counts as closed.
- **Schedule** (optional): the schedule helper of the room, see below.
- **Comfort, night and eco temperature** of the room (defaults 21 °C, 17 °C, 18 °C) and the **lead time**: a warmer level of a block already applies this long before the block starts. It never lowers early.
- **Override expiry** (optional): a policy and duration for this room instead of the global one.

The dialog reminds you to give the HomeKit Bridge and Google Assistant only the room thermostats, not the TRVs; see [Apple Home and Siri](#apple-home-and-siri-homekit-bridge) and [Google Assistant without Home Assistant Cloud](#google-assistant-without-home-assistant-cloud). Change a room later with **Change room** ("Raum ändern") on its sub-entry.

### Schedules

A schedule is a native `schedule` helper and can belong to several rooms. The easiest way is the panel: on the room page under **Rooms** ("Räume") choose **+ Create new schedule …** ("+ Neuen Zeitplan anlegen …"). It creates a helper named "Heizung <room>" from the templates standard week, empty or a copy of another schedule, and assigns it to the room. You can also assign any existing schedule helper there or in the room dialog.

- During a block the level of the block applies, outside the blocks eco.
- The level is stored in the additional data of the block under the key `level`: `night` for night; a block without `level` (or with `level: comfort`) is comfort. Blocks created in the panel carry it already. Schedules edited in the panel stay editable in the schedule editor of Home Assistant.
- A change to a schedule applies to all its rooms at once.

### Room without a schedule

A room without a schedule, or whose schedule helper is missing or unavailable, holds **eco** with the reason "No schedule – Eco" ("Kein Zeitplan – Eco"). All other rules still apply: window open, off, manual override, house mode and away. Because there is no block boundary, off and a manual override end after the override-expiry duration of the room (default 3 h). The room page in the panel then says "<room> has no schedule and holds eco." and offers **Create schedule** ("Zeitplan anlegen").

## Daily use

- **Manual override**: changing the target of a room thermostat (knob, Siri, Google, app) switches the room to `heat` with that target. Targets are rounded to whole degrees (21.5 → 22). The room returns to `auto` by the override-expiry policy: at the next block boundary, after the duration, or at the earlier of both (default, 3 h).
- **Auto** ends an override or off right away.
- **Off** holds frost protection until the next block boundary.
- The attributes of the room thermostat show the reason, the override expiry and the active level.

### Heating panel

The panel "Heizung" ("Heating") appears in the sidebar for admins once the integration is set up. It is built for phones and works in the Home Assistant app.

- **Overview** ("Übersicht"): every room with current and target temperature, mode and reason, updated live. Tapping a room in heat or off returns it to auto, with 6 seconds to undo. Tapping a room in auto opens its room page. Chips at the top show the house mode and away.
- **Rooms** ("Räume"): per room the schedule assignment, the week with its blocks and a day timeline to add, move, resize and delete blocks and to set their level, copying blocks and days to other days, and "applies also to …" with "split off" for shared schedules. Below are the levels and the lead time ("Stufen und Vorlaufzeit").
- **House** ("Haus"): house mode (automatic, vacation, off), vacation with its end, away with every person and the global temperatures for away, vacation and frost protection.

### House mode, vacation and away

The house device provides:

- **House mode** (`select`): `auto`, `vacation`, `off`. Off means frost protection everywhere; vacation needs a vacation end in the future.
- **Vacation end** (`datetime`): when it passes, the house mode returns to `auto`.
- **Away** (`binary_sensor`): on when all configured persons are not home for the presence delay. An unknown or unavailable person counts as home.

A manual override wins over house off, vacation and away, so it gets warm when someone comes home early.

### Service `climate_control.start_vacation`

Sets the vacation end and switches the house mode to vacation in one step, for automations and scripts. All rooms get the vacation temperature until the end, then the house returns to automatic.

```yaml
action: climate_control.start_vacation
data:
  end: "2026-12-27 18:00:00"
```

| Field | Required | Meaning |
|---|---|---|
| `end` | yes | When the vacation ends. Without a time zone it is the local time of Home Assistant. |

An end that is not in the future is refused ("The vacation end must be in the future.") and changes nothing. To end a vacation early, set the house mode to `auto`.

### Reasons

Each room has a reason sensor with the reason in plain text, for example "Komfort bis 22:00", "Fenster offen seit 14:03" or "Vorheizen auf Komfort, Beginn 16:30". Its attribute `reason_code` is stable for automations: `comfort`, `night`, `eco`, `preheat`, `override`, `room_off`, `window_open`, `away`, `vacation`, `house_off`, `no_schedule`. Every change of a target also gets a logbook entry with its reason.

### Notifications and repairs

The notification recipients get one message when a window has been open for 20 minutes and when a TRV has been unreachable for 30 minutes. Each event is sent once, events close together come as one message, and nothing is sent when an event resolves or during the quiet time. A TRV unreachable for more than 30 minutes also shows up under **Settings → Repairs**. The diagnostics download of the integration contains the configuration and the current state of every room.

## Apple Home and Siri (HomeKit Bridge)

The TRVs are `climate` entities themselves. If the [HomeKit Bridge](https://www.home-assistant.io/integrations/homekit/) exposes them, Apple Home shows two thermostats per room, and a change at a TRV bypasses the room thermostat. Expose only the room thermostats:

1. Go to **Settings → Devices & services → HomeKit Bridge** and choose **Configure** on the bridge. (When you add a new bridge, choose the domain **Climate** first and then open **Configure** before pairing.)
2. In "Select mode and domains" keep the HomeKit mode **bridge**, set the inclusion mode to **include** and add **Climate** to the domains to include.
3. In "Select the entities to be included" select **only the room thermostats**. If you select no entity, the whole climate domain is included, TRVs included.
4. Finish the dialog. In "Climate accessory configuration" you can keep **Automatic**.

Use the inclusion mode **include**, not exclude: with exclude every new TRV would show up in Apple Home. Hidden entities are not exposed unless they are selected explicitly, so hiding the TRVs in Home Assistant is an additional safeguard.

A bridge set up in YAML uses a filter instead, for example:

```yaml
homekit:
  - filter:
      include_entities:
        - climate.living_room
        - climate.bathroom
```

Use the entity IDs of your room thermostats (Settings → Entities, filter by the integration Climate Control). Apple Home then shows the modes Auto, Heat and Off of each room; Auto ends an override.

## Google Assistant without Home Assistant Cloud

Without Home Assistant Cloud, Google Assistant is connected through the manual setup of the [Google Assistant](https://www.home-assistant.io/integrations/google_assistant/) integration. Follow its section "Manual setup" for the prerequisites (Home Assistant reachable from the internet over HTTPS), the project in the Google Home Developer Console, the service account and the HomeGraph API. Then expose only the room thermostats in `configuration.yaml`:

```yaml
google_assistant:
  project_id: YOUR_PROJECT_ID
  service_account: !include SERVICE_ACCOUNT.json
  report_state: true
  expose_by_default: false
  entity_config:
    climate.living_room:
      expose: true
    climate.bathroom:
      expose: true
```

- `expose_by_default: false` exposes nothing but the entities marked with `expose: true` in `entity_config`, so TRVs and every other entity stay hidden from Google. With `expose_by_default: false`, `exposed_domains` has no effect.
- The rooms in Google Home come from the areas of the room devices; `room` in `entity_config` sets one explicitly.
- After a change run the action `google_assistant.reload` (changing `project_id` or `service_account` needs a restart), then say "Hey Google, sync my devices" or run `google_assistant.request_sync`.

Google has no exact match for every HVAC mode; see "Climate operation modes" in the Google Assistant documentation.

## Development

See [AGENTS.md](AGENTS.md) for the checks (`scripts/check`), the panel build (`scripts/panel`) and the test setup, and [CHANGELOG.md](CHANGELOG.md) for the releases.
