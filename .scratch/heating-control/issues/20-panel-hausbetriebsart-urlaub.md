# 20: Panel: Hausbetriebsart und Urlaub

Spec: `.scratch/heating-control/spec.md`

**What to build:** Im Reiter „Haus“ des Heating Panel stellt der Admin die Hausbetriebsart um (Automatik, Urlaub, Aus). In der Übersicht zeigt ein Chip die Hausbetriebsart und führt in den Reiter „Haus“. Ein Tipp auf Urlaub öffnet ein Blatt mit Enddatum und Uhrzeit (vorbelegt: in 7 Tagen, 18:00, bzw. das gespeicherte Urlaubsende, wenn es in der Zukunft liegt). Erst „Urlaub starten“ schaltet um. Die Panel API setzt Urlaubsende und Hausbetriebsart dabei in einem Befehl. Denselben Weg nutzt der neue Service `climate_control.start_vacation` mit Pflichtfeld `end` für Automationen und Skripte. Der aktuelle Zustand ist immer sichtbar, inklusive „Abwesend“ und des Urlaubsendes. Die Abwesend-Karte listet die konfigurierten Personen mit ihrem Anwesenheitszustand. Gestaltung laut Rückmeldung aus Ticket 16.

**Blocked by:** 12, 17

**Status:** ready-for-agent

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
- **Offen für das Panel-Ticket 20:** Panel-API-Befehl zum Urlaubsstart (ruft `async_start_vacation`), Umschalten der Hausbetriebsart und Ändern des Urlaubsendes über die Panel API, Personenliste mit Anwesenheitszustand, Reiter „Haus“, Chip in der Übersicht, Live-Aktualisierung, Abnahme per Checkliste.
