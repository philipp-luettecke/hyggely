# 03: Ein Raum folgt dem Zeitplan

Spec: `.scratch/heating-control/spec.md`

**What to build:** Der Admin legt im Einrichtungsdialog einen Raum an. Dazu wählt er ein TRV, einen vorhandenen Zeitplan-Helfer, die Temperaturen für Komfort und Eco sowie den Bereich. Daraufhin entsteht ein Gerät mit einem Raum-Thermostat im Modus Auto. Solange ein Block des Zeitplans aktiv ist, gilt Komfort, sonst Eco. Das Raum-Thermostat zeigt die Solltemperatur und die Ist-Temperatur des TRV. Bei jedem Schaltpunkt erhält das TRV die neue Solltemperatur, immer zusammen mit dem Modus `heat`. Gesendet wird nur, wenn der Zustand des TRV abweicht.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Ein Raum lässt sich als Unterpunkt des Haupteintrags anlegen und im Optionsdialog ändern
- [ ] Pro Raum gibt es ein Gerät im gewählten Bereich mit einem Raum-Thermostat, das die Modi `auto`, `heat` und `off` anbietet
- [ ] Im Modus Auto gilt während eines Blocks die Komfort-Temperatur, außerhalb die Eco-Temperatur
- [ ] Bei einem Schaltpunkt wird das TRV mit Solltemperatur und `heat` in einem Aufruf angesteuert
- [ ] Ist das TRV bereits im Sollzustand, wird kein Befehl gesendet
- [ ] Eine Änderung am Zeitplan-Helfer wirkt sofort auf den Raum
- [ ] Die Ist-Temperatur des Raum-Thermostats entspricht der des TRV
- [ ] Szenario-Tests im Test-Home-Assistant mit echtem Zeitplan-Helfer und vorgespulter Zeit decken die Kriterien ab

## Comments

**Modulaufbau (Grundlage für 04, 05, 06, 07, 09, 10, 11, 13):**
- `target_resolver.py`: reine Entscheidungslogik ohne HA-Importe. `RoomSnapshot` rein, `Decision` raus (Solltemperatur, Raum-Modus, TRV-Modus, `Reason` mit Code und Parametern, `reevaluate_at`). Neue Eingaben kommen als Felder mit Standardwert in `RoomSnapshot` und als Regel an ihrer Stelle der Rangfolge in `resolve()`.
- `schedule_reader.py`: liefert `ScheduleLevel` (Stufe, nächster Schaltpunkt) und meldet Änderungen am Helfer.
- `room_controller.py`: ein Controller pro Raum. Abonniert die Eingaben, hält Raum-Modus, Übersteuerungstemperatur und Rückfallzeit, ruft den Resolver auf, plant die Neubewertung und sendet nur bei Abweichung. `heat` geht immer als `climate.set_temperature` mit `hvac_mode: heat`, `off` als `climate.set_hvac_mode`. Bewertungen laufen über einen Lock nacheinander, damit am Schaltpunkt kein Befehl doppelt rausgeht.
- `climate.py`: dünnes Raum-Thermostat, liest nur den Controller und reicht Befehle durch.
- `__init__.py`: `entry.runtime_data.rooms` (Subentry-ID → Controller), Gerät pro Raum, Update-Listener lädt bei jeder Änderung neu.

**Schedule Reader in 03:** Er liest nur Zustand und `next_event` des Helfers (`on` → Komfort, `off` → Eco). Für 03 reicht das, weil jeder Schaltpunkt ein Zustandswechsel des Helfers ist. Ticket 04 stellt auf die Blöcke aus `schedule.get_schedule` um (Stufe `level`, Vorlaufzeit, eigener nächster Schaltpunkt) und sollte dann zusätzlich `state_reported` abonnieren, weil Änderungen an künftigen Blöcken nicht immer ein `state_changed` erzeugen. Ist `next_event` bereits erreicht, der Helfer aber noch nicht umgeschaltet, liefert der Reader nichts. Der Controller wartet dann auf die Zustandsänderung des Helfers, statt kurz einen veralteten Sollwert zu senden.

**Heizen und Aus am Raum-Thermostat (minimal):** HA verlangt Handler für `set_temperature` und `set_hvac_mode`, sobald Solltemperatur und die Modi `heat`/`off` angeboten werden. Umgesetzt ist das einfachste spec-konforme Verhalten: Eine Temperatur oder `heat` (mit aktuellem Sollwert) übersteuert bis zum nächsten Schaltpunkt, also wie Rückfallregel `next_block`. `off` setzt Frostschutz und das TRV auf `off`, ebenfalls bis zum nächsten Schaltpunkt. `auto` beendet beides sofort. Ticket 06 ergänzt Rückfallregeln, Dauer, Wiederherstellung nach Neustart und Grund; Ticket 07 die Wiederherstellung von Aus. Aktuell gehen Übersteuerung und Aus beim Neuladen des Eintrags (z. B. Optionsänderung) verloren.

**Raum-Daten:** Alles liegt in `data` des Subentrys (Subentries haben keine `options`): `trvs` (Liste), `schedule`, `comfort_temperature`, `eco_temperature`, `area`; der Name ist der Titel. Der Dialog erlaubt bisher genau ein TRV, gespeichert wird trotzdem eine Liste. Für Ticket 09 genügt `multiple=True` im Selektor und das Entfernen der Umwandlung in `_room_data()`/`async_step_reconfigure()`.

**Standardwerte:** Komfort 21 °C, Eco 18 °C (Spec nennt keine). Bitte bei Bedarf anpassen.

**Entity-ID:** HA 2026.11 setzt den Bereichsnamen vor die Entity-ID. Raum „Wohnzimmer“ im Bereich „Wohnzimmer“ ergibt `climate.wohnzimmer_wohnzimmer`; der Anzeigename bleibt „Wohnzimmer“ (getestet). Tests finden das Raum-Thermostat deshalb über den Subentry (`tests/scenario.py: room_entity_id`).

**Optionsdialog des Haupteintrags:** `OptionsFlowWithReload` verträgt keinen Update-Listener. Deshalb ist es jetzt ein normaler `OptionsFlow`, und der Update-Listener lädt bei Optionen und bei jedem Hinzufügen, Ändern oder Entfernen eines Raums neu.

**Bewusst offen (spätere Tickets):** Ein fehlendes oder nicht erreichbares TRV bekommt keinen Befehl. Es wird auch nicht nachgesendet, wenn es zurückkommt (13). Ohne Zustand des Zeitplan-Helfers fällt keine Entscheidung. Das Manifest hat `after_dependencies: ["schedule"]`, damit die Helfer beim Start vor den Räumen da sind.

**Tests:** `tests/scenario.py` enthält Uhr (Europe/Berlin), Zeitplan-Helfer über die nativen Websocket-Befehle (`schedule/create`/`update`), Haupteintrag, Raum-Dialog und das Beispiel-Wohnzimmer. `expected_lingering_timers` ist global erlaubt, weil Zeitplan-Helfer und Räume einen Timer bis zum nächsten Schaltpunkt halten.
