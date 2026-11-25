# 17: Panel-Gerüst mit Raumübersicht

Spec: `.scratch/heating-control/spec.md`

**What to build:** Die Integration registriert in der Seitenleiste den Eintrag „Heizung“, der nur für Admins sichtbar ist, und liefert das Heating Panel als JavaScript-Modul aus. Das Panel hat drei Reiter: Übersicht, Räume und Haus; dieses Ticket füllt die Übersicht, die Tickets 18 und 19 die Raumseite unter „Räume“, Ticket 20 den Reiter „Haus“. Die Übersicht zeigt für das Handy optimiert alle Räume mit Ist-Temperatur, Solltemperatur, Modus und Grund und aktualisiert sich live. Antippen einer laufenden Übersteuerung oder von Aus setzt den Raum auf Auto zurück: ohne Nachfrage, mit 6 Sekunden „Rückgängig“. Das Panel sendet das Beenden erst nach Ablauf dieser 6 Sekunden, beim Verlassen des Panels sofort. Ein Tipp auf einen Raum in Auto bewirkt in diesem Ticket nichts (Sprung auf die Raumseite in Ticket 18). Während der Vorlaufzeit nennt der Grund das Vorheizen („Vorheizen auf Komfort, Beginn 16:30“) statt „Komfort bis 22:00“. Das Panel spricht nur mit der Panel API der Integration und enthält keine Heizlogik. Interne `ha-*`-Komponenten des Frontends setzt es nicht voraus. Gestaltung laut Rückmeldung aus Ticket 16.

**Blocked by:** 05, 06, 16

**Status:** done

- [ ] Der Seitenleisten-Eintrag „Heizung“ erscheint nach dem Einrichten der Integration nur für Admins
- [ ] Das Panel hat die Reiter Übersicht, Räume und Haus
- [ ] Die Panel API liefert eine Raumübersicht und meldet Änderungen per Abonnement. Für Nicht-Admins ist sie gesperrt
- [ ] Das Panel zeigt alle Räume mit Ist, Soll, Modus und Grund und aktualisiert sich ohne Neuladen
- [ ] Antippen beendet Übersteuerung oder Aus über die Panel API, ohne Nachfrage
- [ ] Nach dem Antippen bietet das Panel 6 Sekunden lang „Rückgängig“. Der Befehl geht erst danach raus (beim Verlassen des Panels sofort), Rückgängig verwirft ihn
- [ ] Während der Vorlaufzeit liefert der Grund-Sensor den neuen Grund-Code `preheat` mit Stufe und Blockbeginn („Vorheizen auf Komfort, Beginn 16:30“). Ab Blockbeginn gilt wieder „Komfort bis …“
- [ ] Das Panel funktioniert in der Home-Assistant-App auf iOS und Android
- [ ] Der Build des Panels ist in die automatischen Prüfungen integriert
- [ ] Tests im Test-Home-Assistant decken die Panel API und den Grund `preheat` ab, das Panel selbst ist per Checkliste auf dem Handy abgenommen

## Comments

**Rückmeldung aus Ticket 16 (25.11.2026):** Fragen 4, 8 und 12 (drei Reiter, Vorbild ist die Aufteilung „3R“ im Prototyp auf `prototype/15-panel`).

**Panel und Panel API (Branch `ticket/17-panel-geruest`):** Seitenleisten-Eintrag „Heizung“ (Englisch „Heating“, je nach Sprache von Home Assistant), Symbol `mdi:radiator`, URL `/climate-control`, nur für Admins (`require_admin`). `panel.py` registriert das Panel beim Einrichten des Haupteintrags und entfernt es beim Entladen; das Modul liegt unter `/climate_control/frontend/heating-panel.js?v=<Hash>`, sodass Handys nach einem Update sofort die neue Fassung laden. Das Manifest hängt jetzt von `frontend`, `http`, `panel_custom` und `websocket_api` ab; für die Tests ist `home-assistant-frontend` (Version passend zu HA 2026.11.2) Entwicklungsabhängigkeit. Panel API: `climate_control/rooms/subscribe` sendet sofort alle Räume (`room_id`, `name`, `current_temperature`, `target_temperature`, `room_mode`, `reason` als Text in der Sprache von HA, `reason_code`) und danach nach jeder Änderung die ganze Liste, auch über ein Neuladen des Eintrags hinweg (Signal `SIGNAL_ROOMS_CHANGED` aus `const.py`, gesendet bei jeder Änderung eines Raums und am Ende des Einrichtens). `climate_control/room/return_to_auto` (`room_id`) beendet Übersteuerung oder Aus; unbekannter Raum ergibt `room_not_found`. Beide Befehle sind für Nicht-Admins gesperrt (`unauthorized`).

**Übersicht und Rückgängig:** Karten mit Ist, Soll, Modus-Chip und Grund, farbiger Rand nach Grund wie im Prototyp. Ein Tipp auf einen Raum in Heizen oder Aus zeigt 6 Sekunden „<Raum> kehrt zu Auto zurück – Rückgängig“; der Befehl geht erst danach raus. Sofort gesendet wird beim Verlassen des Panels, beim Wechsel des Reiters, wenn die App in den Hintergrund geht (`visibilitychange`, `pagehide`) und wenn während der 6 Sekunden ein zweiter Raum angetippt wird (dessen Rückgängig ersetzt das erste). Ein Tipp auf einen Raum in Auto bewirkt nichts. Auf schmalen Bildschirmen öffnet ein eigener Menüknopf die Seitenleiste (`hass-toggle-menu`); interne `ha-*`-Komponenten werden nicht verwendet, Farben kommen aus dem Theme.

**Grund `preheat`:** `ScheduleLevel` hat das neue Feld `preheat_start` (Beginn des Blocks, auf den vorgeheizt wird). Der Target Resolver liefert dann den Code `preheat` mit `level` und `start` und plant eine Neubewertung zum Blockbeginn, ab dem wieder „Komfort bis …“ gilt. Texte: „Vorheizen auf {level}, Beginn {start}“ / „Preheating to {level}, starts {start}“; `{level}` kommt aus dem Text des gleichnamigen Grund-Codes („Komfort“, „Nacht“). Der Diagnose-Export zeigt `preheat_start` im Schnappschuss.

**Nahtstellen für 18, 19 und 20:** Jedes Ticket ändert nur eigene Dateien.
- Raumseite (`frontend/src/rooms/rooms-tab.ts`, Raum-Chips und Kopf mit Soll und Grund sind fertig): Abschnitt Zeitplan in `rooms/schedule-section.ts` (Element `cc-room-schedule-section`, 18), Abschnitt Stufen und Vorlaufzeit in `rooms/levels-section.ts` (`cc-room-levels-section`, 19). Beide bekommen `.hass` und `.room` (Eintrag der Raumübersicht) und zeigen bisher Titel und „Folgt in einer späteren Version.“
- Reiter Haus (`frontend/src/house/house-tab.ts`): `house/house-mode-section.ts` (`cc-house-mode-section`, 20: Betriebsart, Urlaub, Abwesend mit Personen) und `house/global-temperatures-section.ts` (`cc-global-temperatures-section`, 19). Zusätzlich für 20 die Chips über den Räumen der Übersicht in `house/house-status.ts` (`cc-house-status`, bisher leer).
- Sprung aus der Übersicht (18): In `overview/overview-tab.ts`, Methode `_tap`, für Räume in Auto `navigate(this, "rooms", room.room_id)` aus `navigation.ts` aufrufen; die Hülle wechselt dann auf die Raumseite. Die Zeile ist mit „ticket 18“ markiert.
- Panel API im Frontend: je Ticket eine eigene Datei unter `frontend/src/api/` (17: `api/rooms.ts`). Texte (de/en) stehen in jeder Komponente selbst (`localize()` aus `i18n.ts`), es gibt keine gemeinsame Textdatei.
- Panel API in Python: Paket `panel_api/`, je Ticket ein Modul mit `async_register_commands(hass)`, das `panel_api/__init__.py` bereits aufruft: `schedules.py` (18), `levels.py` (19), `house.py` (20), alle drei noch leer. Gemeinsam: `panel_api/common.py` mit `loaded_runtime_data()` und `room_controller_or_error()`. Registriert wird einmal in `async_setup`; Befehle finden den Haupteintrag zur Laufzeit. Schreibt ein Befehl Subentry-Optionen (19), lädt der Eintrag neu, und das Abonnement der Raumübersicht liefert danach die neuen Werte (per Test abgesichert).
- Unvermeidliche gemeinsame Datei: das gebaute Modul `heating-panel.js`. Es ist nicht minifiziert und nach Quelldateien gegliedert, sodass Git Änderungen verschiedener Abschnitte meist ohne Konflikt zusammenführt. Bei einem Konflikt eine Seite nehmen, `scripts/panel build` ausführen und committen; `scripts/check` meldet ein veraltetes Modul.

**Build-Entscheidung:** TypeScript mit Lit 3, gebündelt mit esbuild (`frontend/build.mjs`, Ziel ES2021/Safari 15, ein ESM-Modul, nicht minifiziert, ca. 42 KB), Typprüfung mit `tsc`. Das gebaute Modul `custom_components/climate_control/frontend/heating-panel.js` ist **eingecheckt**, weil HACS direkt aus dem Repository installiert und ein Testsystem ohne Node auskommen soll. Reproduzierbar ist es trotzdem: `scripts/panel check` (Teil von `scripts/check`) prüft die Typen, baut neu und schlägt fehl, wenn das eingecheckte Modul abweicht; `scripts/panel build` schreibt es neu. Versionen sind fest (`package-lock.json`, `npm ci`). Unter WSL beschädigt npm Pakete auf dem Windows-Laufwerk, deshalb baut `scripts/panel` in einer Kopie unter `~/.cache/climate-control/venvs/<Hash>/frontend`. Die Registry in WSL löst ohne DNS-Workaround auf; in `unshare` scheitert npm an `chown`. Der Lockfile enthält `registry.npmjs.org`, npm ersetzt das lokal durch die konfigurierte Registry. CI: `actions/setup-node@v5` mit Node 22 und npm-Cache vor `./scripts/check`. Beschrieben in `AGENTS.md`. Ob Ticket 21 statt des eingecheckten Moduls ein Release-Zip baut, kann dort entschieden werden.

**Tests:** `tests/test_heating_panel.py` (Seitenleiste nur für Admins, Titel je Sprache, Modul wird ausgeliefert, Eintrag verschwindet beim Entladen), `tests/test_panel_api.py` (Raumübersicht mit zwei Räumen, Live-Meldung einer Übersteuerung, Abonnement über ein Neuladen, Sperre für Nicht-Admins, Zurück auf Auto aus Heizen und aus Aus, unbekannter Raum), `tests/test_reason.py` (Vorheizen deutsch und englisch, ab Blockbeginn wieder Komfort, Texte vorhanden). 220 Tests grün.

**Offen: Abnahme auf dem Handy** (Checkliste, iOS und Android in der Home-Assistant-App, als Kommentar hier ablegen):
- [ ] „Heizung“ erscheint in der Seitenleiste des Admin-Kontos, nicht bei einem Nicht-Admin
- [ ] Menüknopf öffnet die Seitenleiste; Reiter Übersicht, Räume, Haus lassen sich wechseln
- [ ] Übersicht zeigt alle Räume mit Ist, Soll, Modus und Grund; Drehen am Knopf bzw. Siri erscheint ohne Neuladen (Drehknopf bis ca. 1 Minute Verzögerung)
- [ ] Tipp auf Heizen/Aus: Hinweis mit „Rückgängig“, nach 6 Sekunden Auto; „Rückgängig“ lässt den Raum unverändert
- [ ] Tipp, dann sofort die App in den Hintergrund oder ein anderes Panel: Raum ist sofort auf Auto
- [ ] Während der Vorlaufzeit „Vorheizen auf Komfort, Beginn …“, ab Blockbeginn „Komfort bis …“
- [ ] Dunkles Theme lesbar, nichts verdeckt von Notch oder Home-Leiste

**Abgeschlossen:** Merge-Commit `4cfd8d4` auf `feat/heating-control`. Ergebnis: Panel „Heizung“ nur für Admins mit drei Reitern und live aktualisierter Raumübersicht, Zurück auf Auto mit 6 Sekunden Rückgängig, Grund `preheat`, Panel-Build in `scripts/check` und CI, Nahtstellen für 18–20 angelegt; 220 Tests grün. Die Abnahme auf dem Handy steht noch aus (Checkliste oben).
