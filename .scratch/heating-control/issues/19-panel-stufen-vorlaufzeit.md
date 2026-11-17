# 19: Panel: Stufentemperaturen und Vorlaufzeit

Spec: `.scratch/heating-control/spec.md`

**What to build:** Im Heating Panel kann der Admin pro Raum die Temperaturen von Komfort, Nacht und Eco sowie die Vorlaufzeit ändern. Die Änderungen werden in die Raum-Einstellungen der Integration geschrieben und wirken sofort. Die globalen Temperaturen für Abwesend, Urlaub und Frostschutz sind ebenfalls änderbar. Gestaltung laut Rückmeldung aus Ticket 16.

**Blocked by:** 04, 17

**Status:** ready-for-agent

- [ ] Pro Raum lassen sich Komfort, Nacht, Eco und Vorlaufzeit im Panel ändern
- [ ] Die globalen Temperaturen für Abwesend, Urlaub und Frostschutz lassen sich im Panel ändern
- [ ] Die Werte sind auf den Bereich der TRVs begrenzt (5–25 °C laut Ticket 01). Die Schrittweite folgt dem Stand in der Spec (Further Notes)
- [ ] Änderungen erscheinen danach auch im Optionsdialog der Integration
- [ ] Änderungen wirken sofort auf die Solltemperatur des Raums
- [ ] Tests im Test-Home-Assistant decken die Panel API ab, das Panel ist per Checkliste abgenommen
