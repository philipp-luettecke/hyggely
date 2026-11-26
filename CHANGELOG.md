# Changelog

All notable changes are listed here. Versions follow [Semantic Versioning](https://semver.org/); the version in `custom_components/hyggely/manifest.json` and the release tag are the same.

## 0.1.0 (not released yet)

First release. Requires Home Assistant 2026.11.

### Rooms and schedules

- Main entry with the global settings (persons and presence delay, notification recipients and quiet time, away, vacation and frost protection temperatures, override expiry, window delay) and rooms as sub-entries, all set up and changed in the UI.
- Room thermostat (`climate`) per room with the modes `auto`, `heat` and `off`, as a device in the area of the room. Several TRVs per room get the same target; the current temperature is the mean of the reachable ones.
- Native `schedule` helpers as schedules, shared by several rooms if wanted. Blocks carry the level comfort or night in their additional data (`level`), eco applies outside the blocks. Comfort, night and eco temperatures and the lead time per room; a warmer level applies the lead time before its block, the room never lowers early.
- The schedule is optional: a room without a schedule, or whose helper is missing or unavailable, holds eco ("No schedule – Eco"); all other rules still apply.
- Targets in whole degrees from 5 to 25 °C.

### Overrides and rules

- A turn of the knob at any TRV, Siri, Google or the app becomes a manual override of the whole room, rounded to whole degrees. It ends at the next block boundary, after a duration or at the earlier of both (default: earlier, 3 h), globally or per room. Off holds frost protection until the next block boundary. Without a block boundary both end after the override-expiry duration.
- Window open (after 60 s) gives frost protection and restores the previous state when closed, including an override.
- Away when all persons are gone for 30 minutes, house mode `auto`/`vacation`/`off` with a vacation end. An override wins over house off, vacation and away.
- Service `hyggely.start_vacation` sets the vacation end and starts the vacation in one step.
- Overrides, off and the house mode survive a restart. Unreachable TRVs get their target again once they are back, staggered after a restart; a command a TRV did not take is sent once more.

### Transparency

- Reason sensor per room with the reason in plain text (German and English) and a stable `reason_code`, logbook entries for every new target, diagnostics download.
- Notifications for a window open for 20 minutes and a TRV unreachable for 30 minutes: once per event, bundled, held back during the quiet time. Repair issue for a TRV unreachable for more than 30 minutes.

### Heating panel

- Sidebar panel "Heizung" ("Heating") for admins, built for phones: overview with live room status and a tap back to auto (with undo), room pages with week overview and day timeline to edit blocks and levels, copying blocks and days, creating, assigning and splitting off schedules, levels and lead time; house tab with house mode, vacation, away with persons and the global temperatures.

### Setup

- The room setup dialog reminds you to give HomeKit Bridge and Google Assistant only the room thermostats, not the TRVs. The README explains both settings and the installation via HACS or by hand.
- Own brand icon in Home Assistant and HACS. Licensed under the Apache License 2.0.
