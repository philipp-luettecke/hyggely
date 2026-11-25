# 19: Panel: Stufentemperaturen und Vorlaufzeit

Spec: `.scratch/heating-control/spec.md`

**What to build:** Auf der Raumseite im Reiter „Räume“ kann der Admin unter dem Zeitplan die Temperaturen von Komfort, Nacht und Eco sowie die Vorlaufzeit des Raums ändern. Die Änderungen werden in die Raum-Einstellungen der Integration geschrieben und wirken sofort. Die globalen Temperaturen für Abwesend, Urlaub und Frostschutz sind im Reiter „Haus“ ebenfalls änderbar. Temperaturen ändern sich mit −/+ in ganzen Grad, die Vorlaufzeit in 15-Minuten-Schritten bis 3 Stunden. Ist Nacht oder Eco wärmer als Komfort, zeigt das Panel einen Hinweis, sperrt aber nicht. Die Schrittweite von 1 °C gilt in der ganzen Integration: im Einrichtungs- und Optionsdialog und am Raum-Thermostat. Gestaltung laut Rückmeldung aus Ticket 16.

**Blocked by:** 04, 17

**Status:** ready-for-agent

- [ ] Pro Raum lassen sich Komfort, Nacht, Eco und Vorlaufzeit auf der Raumseite unter „Räume“ ändern
- [ ] Die globalen Temperaturen für Abwesend, Urlaub und Frostschutz lassen sich im Reiter „Haus“ ändern
- [ ] Die Werte sind auf den Bereich der TRVs begrenzt (5–25 °C laut Ticket 01). Die Schrittweite ist 1 °C (Spec, Further Notes). Vorhandene halbe Werte werden angezeigt, −/+ rundet auf ganze Grad
- [ ] `TEMPERATURE_STEP` ist 1 °C: Einrichtungs- und Optionsdialog sowie `target_temperature_step` des Raum-Thermostats arbeiten in ganzen Grad
- [ ] Die Vorlaufzeit lässt sich in 15-Minuten-Schritten von 0 bis 3 Stunden einstellen
- [ ] Ist Nacht oder Eco wärmer als Komfort, zeigt das Panel einen Hinweis („Nacht ist wärmer als Komfort – gewollt?“), speichert aber trotzdem. Nacht wärmer als Eco bekommt keinen Hinweis
- [ ] Änderungen erscheinen danach auch im Optionsdialog der Integration
- [ ] Änderungen wirken sofort auf die Solltemperatur des Raums
- [ ] Tests im Test-Home-Assistant decken die Panel API ab, das Panel ist per Checkliste abgenommen

## Comments

**Rückmeldung aus Ticket 16 (25.11.2026):** Fragen 9 und 12. Einen eigenen Reiter „Stufen“ gibt es nicht. Die Raumseite teilt sich dieses Ticket mit Ticket 18, den Reiter „Haus“ mit Ticket 20.

**Teil vorgezogen (Branch `ticket/19-temperature-step`):** Umgesetzt ist der reine Integrationsteil ohne Panel: `TEMPERATURE_STEP` in `const.py` ist 1 °C. Damit bieten der Einrichtungs- und Optionsdialog des Haupteintrags (Abwesend, Urlaub, Frostschutz) und der Raum-Dialog beim Anlegen und Ändern (Komfort, Nacht, Eco) ganze Grad an, und das Raum-Thermostat meldet `target_temp_step: 1.0`. Der Bereich 5–25 °C galt schon vorher. Neue Tests in `tests/test_temperature_step.py` prüfen die Schrittweite am Raum-Thermostat und in den Formularen, so wie das Frontend sie bekommt. Szenario-Tests, die Stufen im Dialog auf halbe Grad geändert haben, nutzen jetzt ganze Grad (`test_away.py`, `test_levels_and_lead_time.py`, `test_room_follows_schedule.py`, `test_main_entry.py`). `test_logbook.py` behält 21,5 °C, weil es als einziger Test das Dezimalkomma im Logbuch prüft und vorhandene halbe Werte gültig bleiben. Gemessene Ist-Temperaturen mit halben Grad sind nicht betroffen.

Offen für das Panel-Ticket 19: Stufen und Vorlaufzeit auf der Raumseite, globale Temperaturen im Reiter „Haus“, die Befehle der Panel API dazu, −/+ mit Rundung auf ganze Grad, Vorlaufzeit in 15-Minuten-Schritten bis 3 Stunden, der Hinweis bei Nacht oder Eco wärmer als Komfort und die Abnahme per Checkliste.

Offene Fragen an den Admin, nicht umgesetzt:
1. **Rundung von Werten per Siri oder App.** Ticket 16 (Frage 9) sagt „Werte per Siri oder App werden auf ganze Grad gerundet“. Die Schrittweite allein leistet das nicht: Der Dialog übernimmt eingetippte Werte ungerundet (der Zahlenwähler von Home Assistant rundet nicht), und die HomeKit-Bridge ignoriert `target_temp_step` (sie arbeitet in 0,1 °C, Apple Home zeigt halbe Grad). Ein Aufruf von `climate.set_temperature` mit 21,5 °C landet heute unverändert als Übersteuerung beim TRV. Optionen:
   - **A:** Nicht runden. Ganze Grad gelten nur als Vorgabe für die Bedienoberflächen, halbe Werte per Siri oder Automation wirken wie gewünscht.
   - **B:** Das Raum-Thermostat rundet jede Übersteuerung auf ganze Grad, kaufmännisch (21,5 → 22, 20,5 → 21; nicht Pythons `round`, das 20,5 auf 20 rundet). Siri-„21,5 Grad“ ergibt dann 22 °C.
   - **C:** Wie B, zusätzlich runden die Dialoge beim Speichern.

   Empfehlung: **B.** Das entspricht dem Wortlaut aus Ticket 16 und dem Drehknopf, und es ist auf `RoomClimate.async_set_temperature` begrenzt. Die Dialoge sollten vorhandene halbe Werte wie bisher behalten (also nicht C), passend zu „Vorhandene halbe Werte werden angezeigt“.
2. **Vorlaufzeit im Raum-Dialog.** Die Grenze 0–3 Stunden in 15-Minuten-Schritten ist im Ticket nur für das Panel festgelegt. Der Raum-Dialog nimmt weiterhin jede Dauer an. Empfehlung: im Dialog unverändert lassen; die Vorgabe kann das Panel-Ticket bei Bedarf in die Panel API mitnehmen.

**Entscheidung Admin (25.11.2026):**
1. Rundung: Ja (Variante B). Das Raum-Thermostat rundet jede Übersteuerung, etwa per Siri, HomeKit oder Automation über `climate.set_temperature`, kaufmännisch auf ganze Grad (21,5 → 22, 20,5 → 21; nicht Pythons `round`). Vorhandene halbe Werte in den Dialogen bleiben gültig.
2. Vorlaufzeit im Raum-Dialog: unverändert. Die Grenze 0–3 Stunden in 15-Minuten-Schritten gilt nur im Panel.

**Rundung (Branch `ticket/19-temperature-step`):** `RoomClimate.async_set_temperature` rundet kaufmännisch auf ganze Grad (`floor(x + 0,5)`), also jede Übersteuerung über `climate.set_temperature` (Siri über die HomeKit-Bridge, Google, App, Automationen). Eine Übersteuerung am Drehknopf kommt ohnehin in ganzen Grad an und wird nicht gerundet. Vorhandene halbe Stufenwerte bleiben unverändert und gelten weiter. Tests: `tests/test_temperature_step.py` (21,5 → 22, 20,5 → 21, 21,4 → 21).

**Panel API (`panel_api/levels.py`), nur für Admins:**
- `climate_control/room/levels` (`room_id`) liefert `comfort_temperature`, `night_temperature`, `eco_temperature` und `lead_time_minutes`.
- `climate_control/room/set_levels` (`room_id`, beliebige dieser vier Felder) schreibt nur die übergebenen Werte in die Raum-Einstellungen (Subentry). Der Eintrag lädt neu, der Raum wertet sofort aus, und die Werte stehen danach im Optionsdialog des Raums. Temperaturen 5–25 °C; halbe Werte nimmt die API an, wie die Dialoge. Die Vorlaufzeit ist 0–180 min in 15-Minuten-Schritten, sonst `invalid_format`. Nacht oder Eco wärmer als Komfort wird gespeichert.
- `climate_control/house/temperatures` und `climate_control/house/set_temperatures` (`away_temperature`, `vacation_temperature`, `frost_temperature`, je 5–25 °C) schreiben in die Optionen des Haupteintrags. Alle Räume übernehmen die neuen Werte sofort.
- Unbekannter Raum: `room_not_found`, nicht geladen: `not_loaded`, Nicht-Admin: `unauthorized`. Das Abonnement der Raumübersicht liefert nach dem Neuladen den neuen Sollwert (per Test abgesichert).
- Tests: `tests/test_panel_levels.py` (15 Tests).

**Panel:**
- Raumseite, Abschnitt „Stufen und Vorlaufzeit“ (`rooms/levels-section.ts`): −/+ für Komfort, Nacht und Eco (Punkt in Stufenfarbe) und die Vorlaufzeit („45 min“, „1 h 30 min“). Ein halber Wert wird angezeigt (z. B. „21,5 °C“), −/+ geht auf den nächsten ganzen Grad (21,5 → 22 bzw. 21). Eine Vorlaufzeit außerhalb des Rasters (z. B. 20 min aus dem Dialog) geht auf den nächsten 15-Minuten-Schritt. Die Grenzen sperren den jeweiligen Knopf.
- Ist Nacht oder Eco wärmer als Komfort, steht darunter „Nacht ist wärmer als Komfort – gewollt?“ bzw. „Eco ist wärmer als Komfort – gewollt?“. Gespeichert wird trotzdem, Nacht gegenüber Eco bekommt keinen Hinweis.
- Reiter Haus, Abschnitt „Temperaturen für das ganze Haus“ (`house/global-temperatures-section.ts`): Abwesend, Urlaub und Frostschutz mit −/+, darunter der Hinweis, wann Frostschutz gilt.
- Gespeichert wird 1 Sekunde nach dem letzten Tipp, damit mehrere Tipps nur ein Neuladen auslösen. Beim Verlassen des Panels, beim Wechsel von Raum oder Reiter und wenn die App in den Hintergrund geht, wird sofort gespeichert. Ein Fehler erscheint im Abschnitt, danach lädt er die gespeicherten Werte neu.
- Gemeinsame Bausteine in `frontend/src/stepper.ts` (−/+, Rundung, verzögertes Speichern), API-Aufrufe in `frontend/src/api/levels.ts`. Die Werte werden beim Öffnen des Raums bzw. des Reiters geladen; eine Änderung im Optionsdialog erscheint im offenen Panel erst nach erneutem Öffnen.

**Nebenbei:** Nach dem Merge von Ticket 17 meldete `scripts/check` Ruff-Befunde in Dateien von 17 (`panel.py`, `tests/test_panel_api.py`, Docstring von `panel_api/house.py`). Sie sind hier minimal behoben, ohne die Logik zu ändern.
