# 20: Panel: Hausbetriebsart und Urlaub

Spec: `.scratch/heating-control/spec.md`

**What to build:** Im Reiter „Haus“ des Heating Panel stellt der Admin die Hausbetriebsart um (Automatik, Urlaub, Aus). In der Übersicht zeigt ein Chip die Hausbetriebsart und führt in den Reiter „Haus“. Ein Tipp auf Urlaub öffnet ein Blatt mit Enddatum und Uhrzeit (vorbelegt: in 7 Tagen, 18:00, bzw. das gespeicherte Urlaubsende, wenn es in der Zukunft liegt). Erst „Urlaub starten“ schaltet um. Die Panel API setzt Urlaubsende und Hausbetriebsart dabei in einem Befehl. Denselben Weg nutzt der neue Service `climate_control.start_vacation` mit Pflichtfeld `end` für Automationen und Skripte. Der aktuelle Zustand ist immer sichtbar, inklusive „Abwesend“ und des Urlaubsendes. Die Abwesend-Karte listet die konfigurierten Personen mit ihrem Anwesenheitszustand. Gestaltung laut Rückmeldung aus Ticket 16.

**Blocked by:** 12, 17

**Status:** done

- [ ] Die Hausbetriebsart lässt sich im Panel umschalten
- [ ] Urlaub verlangt ein Enddatum mit Uhrzeit und wird erst mit „Urlaub starten“ aktiv. Das Panel zeigt das Ende an, während des Urlaubs bleibt es änderbar
- [ ] Die Panel API setzt Urlaubsende und Urlaub in einem Befehl und lehnt ein Ende ab, das nicht in der Zukunft liegt
- [ ] Der Service `climate_control.start_vacation` (Feld `end`) setzt Urlaubsende und Urlaub in einem Schritt, mit derselben Ablehnung. Er ist in `services.yaml` und den Übersetzungen beschrieben
- [ ] Ein aktives Abwesend ist im Panel erkennbar
- [ ] Die Abwesend-Karte zeigt jede konfigurierte Person als „zu Hause“, „unterwegs“ oder „unbekannt – zählt als zu Hause“. Die Panel API liefert diese Liste mit
- [ ] Änderungen außerhalb des Panels, etwa per Siri oder Automation, erscheinen sofort im Panel
- [ ] Tests im Test-Home-Assistant decken die Panel API und den Service ab, das Panel ist per Checkliste abgenommen

## Comments

**Rückmeldung aus Ticket 16 (25.11.2026):** Fragen 10 und 11. Kein eigener Service zum Beenden (Hausbetriebsart auf Automatik), kein geplanter Urlaubsbeginn, kein Countdown bis Abwesend. Nach Frage 12 stehen im Reiter „Haus“ auch die globalen Temperaturen; deren Umsetzung gehört zu Ticket 19.

**Teil vorgezogen (Branch `ticket/20-start-vacation`):** Nur der Integrationsteil ohne Panel, parallel zu Ticket 17 (freigegeben laut Handover, Abschnitt „Optional“).

- **Gemeinsame Funktion:** `HouseModeController.async_start_vacation(vacation_end)` in `house_mode.py` setzt Urlaubsende und Hausbetriebsart Urlaub in einem Schritt (eine Speicherung, eine Benachrichtigung der Listener). Ein Ende, das nicht in der Zukunft liegt, wird mit `ServiceValidationError` (`translation_key="vacation_end_must_be_ahead"`) abgelehnt und ändert nichts, auch keinen laufenden Urlaub. Der Panel-API-Befehl aus diesem Ticket soll genau diese Methode aufrufen (`entry.runtime_data.house_mode`).
- **Service:** `climate_control.start_vacation` mit Pflichtfeld `end` (`cv.datetime`, Selektor `datetime`) in `services.py`, registriert in `async_setup` (dafür `CONFIG_SCHEMA = cv.config_entry_only_config_schema`). Ein Ende ohne Zeitzone gilt als Ortszeit. Ist die Integration nicht geladen, lehnt der Service mit `not_loaded` ab. Beschreibung in `services.yaml`, Icon in `icons.json`, Texte für Service, Feld und beide Fehlermeldungen in `strings.json`, `translations/en.json` und `translations/de.json`.
- **Tests:** `tests/test_start_vacation.py`: Urlaub bis Freitag 18:00 per Service mit Rückkehr zu Automatik, Ablehnung eines Endes in der Vergangenheit und genau jetzt, Ablehnung während eines laufenden Urlaubs lässt ihn unverändert, Ablehnung ohne geladene Integration, Texte auf Deutsch und Englisch. Ein Test über `async_get_all_descriptions` scheitert im Test-HA an einer fremden Integration (fehlendes Paket `hassil`); `services.yaml` prüft hassfest in der CI.
- **Entscheidung mit Alternative (bitte bestätigen):** Eigener Fehler-Schlüssel `vacation_end_must_be_ahead` („Das Urlaubsende muss in der Zukunft liegen.“) statt `vacation_end_not_ahead`. Grund: Dessen Text „… Setze zuerst das Urlaubsende.“ passt nur zur Auswahl-Entität, nicht zu einem Aufruf, der das Ende selbst mitbringt. Alternative: denselben Schlüssel verwenden und dessen Text auf den ersten Satz kürzen. Empfehlung: eigener Schlüssel, wie umgesetzt; das Panel nutzt ihn mit.
- **Offen für das Panel-Ticket 20 (Stand des Teil-Branches):** Panel-API-Befehl zum Urlaubsstart (ruft `async_start_vacation`), Umschalten der Hausbetriebsart und Ändern des Urlaubsendes über die Panel API, Personenliste mit Anwesenheitszustand, Reiter „Haus“, Chip in der Übersicht, Live-Aktualisierung, Abnahme per Checkliste.

**Entscheidung Admin (25.11.2026):** Eigener Fehlerschlüssel `vacation_end_must_be_ahead` („Das Urlaubsende muss in der Zukunft liegen.“) wie umgesetzt, für den Service und den Panel-API-Befehl. `vacation_end_not_ahead` bleibt bei der Auswahl-Entität „Hausbetriebsart“.

**Panel API Haus (`panel_api/house.py`, nur für Admins):**
- `climate_control/house/subscribe` sendet sofort und nach jeder Änderung den Zustand des Hauses, auch über ein Neuladen des Eintrags hinweg. Neu angebunden wird beim Signal `SIGNAL_ROOMS_CHANGED` am Ende des Einrichtens. Inhalt: `house_mode`, `vacation_end` (Ortszeit von HA mit Offset, z. B. `2026-11-20T18:00:00+01:00`, sonst `null`), `away` und `persons` (`entity_id`, `name`, `presence` = `home`/`not_home`/`unknown`). Gemeldet werden Änderungen der Hausbetriebsart und des Urlaubsendes (auch per Siri oder Automation), des Abwesend-Zustands und jedes Anwesenheitszustands.
- `climate_control/house/set_mode` (`house_mode` = `auto` oder `off`). Urlaub ist hier bewusst nicht wählbar, weil er nur mit Ende startet.
- `climate_control/house/start_vacation` (`end`; ohne Zeitzone gilt die Ortszeit von HA) ruft `HouseModeController.async_start_vacation` auf, dieselbe Funktion wie der Service. Ein Ende, das nicht in der Zukunft liegt, ergibt den Fehlercode `vacation_end_must_be_ahead`. Während des Urlaubs verschiebt derselbe Befehl das Ende.
- Die Einstufung der Personen steckt in `Presence.person_presence()` (`presence.py`), damit Liste und Abwesend-Regel übereinstimmen. Zone oder `not_home` gilt als unterwegs; unbekannt, nicht verfügbar oder fehlend gilt als „unbekannt – zählt als zu Hause“.

**Panel:** API-Aufrufe in `frontend/src/api/house.ts`.
- Reiter „Haus“ (`house/house-mode-section.ts`): Umschalter Automatik/Urlaub/Aus mit Erklärung und dem Hinweis, dass eine Übersteuerung trotzdem wirkt. Ein Tipp auf Urlaub öffnet ein Blatt mit Datum und Uhrzeit, vorbelegt mit dem gespeicherten Ende, falls es in der Zukunft liegt, sonst mit in 7 Tagen um 18:00 (Uhr des Handys). Erst „Urlaub starten“ schaltet um. Während des Urlaubs stehen „Urlaub bis Fr., 20.11., 18:00, danach Automatik.“ und „Ende ändern“ da (gleiches Blatt mit „Speichern“).
- Fehler wie ein Ende in der Vergangenheit erscheinen im Blatt. Die Abwesend-Karte zeigt Ja/Nein, eine Erklärung und alle Personen mit „zu Hause“, „unterwegs“ oder „unbekannt – zählt als zu Hause“. Ohne Personen gibt es einen Hinweis auf die Optionen.
- Übersicht (`house/house-status.ts`): Chips „Haus: Automatik / Urlaub bis … / Aus“ und „Abwesend / Jemand zu Hause“, hervorgehoben, wenn nicht Automatik bzw. wenn abwesend. Ein Tipp führt in den Reiter „Haus“.
- Das Urlaubsende wird als Wanduhrzeit von HA angezeigt, unabhängig von der Zeitzone des Handys.

**Nebenbei:** Beim Mergen von 17 lagen zwei `async_setup` in `__init__.py`; jetzt registriert eine Funktion Panel API und Service. Ruff-Befunde aus 17 (`levels.py`, `panel.py`, `tests/test_panel_api.py`) waren identisch schon auf `feat/heating-control` behoben (`b8fbc4c`).

**Tests:** `tests/test_panel_api_house.py` (11) prüft:
- Zustand mit drei Personen (zu Hause, in einer Zone, unbekannt).
- Live-Meldung bei Haus aus per Entität, bei einer Person, die geht, und beim Eintritt von Abwesend.
- Abonnement über ein Neuladen mit neuer Personenliste.
- Umschalten auf Aus und Automatik; Urlaub direkt wird abgelehnt.
- Urlaub mit Ende in einem Befehl, Ende während des Urlaubs verschieben, Ablehnung eines Endes in der Vergangenheit.
- Sperre aller drei Befehle für Nicht-Admins.

Dazu `tests/test_start_vacation.py` (7) für den Service. Insgesamt 238 Tests grün. Eine Sichtprüfung im Headless-Browser war in dieser Umgebung nicht möglich, die Optik kommt über die Checkliste.

**Abnahme auf dem Handy** (iOS und Android in der Home-Assistant-App, Ergebnis als Kommentar hier ablegen):
- [ ] Übersicht: Chips „Haus: Automatik“ und „Jemand zu Hause“; ein Tipp führt in den Reiter „Haus“
- [ ] Reiter „Haus“: Aus wählen, alle Räume zeigen Frostschutz, der Chip in der Übersicht wird „Haus: Aus“; zurück auf Automatik
- [ ] Tipp auf Urlaub öffnet das Blatt mit in 7 Tagen 18:00; „Abbrechen“ lässt die Hausbetriebsart unverändert
- [ ] Datums- und Uhrzeitauswahl funktioniert mit der nativen Auswahl von iOS und Android
- [ ] Ein Ende in der Vergangenheit zeigt „Das Urlaubsende muss in der Zukunft liegen.“ im Blatt
- [ ] „Urlaub starten“: Anzeige „Urlaub bis …, danach Automatik.“, Räume zeigen „Urlaub bis …“, Chip „Haus: Urlaub bis …“
- [ ] „Ende ändern“ ist mit dem aktuellen Ende vorbelegt und verschiebt es
- [ ] Urlaubsende per Entität oder Siri ändern bzw. Hausbetriebsart per Siri umschalten: das Panel folgt ohne Neuladen
- [ ] Abwesend-Karte: alle Personen mit „zu Hause“, „unterwegs“ oder „unbekannt – zählt als zu Hause“; Handy verlässt das Haus, Zustand wechselt live, nach der Abwesenheitsverzögerung „Abwesend: Ja“ und Chip „Abwesend“
- [ ] Blatt auf dem Handy: Tastatur bzw. Auswahl verdeckt die Knöpfe nicht, nichts verdeckt von Notch oder Home-Leiste, dunkles Theme lesbar
- [ ] Service `climate_control.start_vacation` erscheint im Automationseditor mit Feld „Ende“ (Datum und Uhrzeit)

**Abgeschlossen:** Merge-Commit `372563a` auf `feat/heating-control`. Ergebnis: Reiter „Haus“ mit Hausbetriebsart, Urlaub erst nach Wahl des Endes, änderbarem Urlaubsende und Abwesend-Karte mit Personen, Chips in der Übersicht, Panel API Haus mit Live-Meldungen, Service `climate_control.start_vacation` über dieselbe Funktion; 238 Tests grün. Die Abnahme auf dem Handy steht noch aus (Checkliste oben).
