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
