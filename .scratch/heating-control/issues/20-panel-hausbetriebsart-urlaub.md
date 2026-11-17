# 20: Panel: Hausbetriebsart und Urlaub

Spec: `.scratch/heating-control/spec.md`

**What to build:** Oben im Heating Panel stellt der Admin die Hausbetriebsart um (Automatik, Urlaub, Aus). Für Urlaub wählt er ein Enddatum mit Uhrzeit. Der aktuelle Zustand ist immer sichtbar, inklusive „Abwesend“ und des Urlaubsendes. Gestaltung laut Rückmeldung aus Ticket 16.

**Blocked by:** 12, 17

**Status:** ready-for-agent

- [ ] Die Hausbetriebsart lässt sich im Panel umschalten
- [ ] Urlaub verlangt ein Enddatum mit Uhrzeit, und das Panel zeigt es an
- [ ] Ein aktives Abwesend ist im Panel erkennbar
- [ ] Änderungen außerhalb des Panels, etwa per Siri oder Automation, erscheinen sofort im Panel
- [ ] Tests im Test-Home-Assistant decken die Panel API ab, das Panel ist per Checkliste abgenommen
