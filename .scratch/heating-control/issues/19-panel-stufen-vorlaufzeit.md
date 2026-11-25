# 19: Panel: Stufentemperaturen und Vorlaufzeit

Spec: `.scratch/heating-control/spec.md`

**What to build:** Im Heating Panel kann der Admin pro Raum die Temperaturen von Komfort, Nacht und Eco sowie die Vorlaufzeit ändern. Die Änderungen werden in die Raum-Einstellungen der Integration geschrieben und wirken sofort. Die globalen Temperaturen für Abwesend, Urlaub und Frostschutz sind ebenfalls änderbar. Temperaturen ändern sich mit −/+ in ganzen Grad, die Vorlaufzeit in 15-Minuten-Schritten bis 3 Stunden. Ist Nacht oder Eco wärmer als Komfort, zeigt das Panel einen Hinweis, sperrt aber nicht. Die Schrittweite von 1 °C gilt in der ganzen Integration: im Einrichtungs- und Optionsdialog und am Raum-Thermostat. Gestaltung laut Rückmeldung aus Ticket 16.

**Blocked by:** 04, 17

**Status:** ready-for-agent

- [ ] Pro Raum lassen sich Komfort, Nacht, Eco und Vorlaufzeit im Panel ändern
- [ ] Die globalen Temperaturen für Abwesend, Urlaub und Frostschutz lassen sich im Panel ändern
- [ ] Die Werte sind auf den Bereich der TRVs begrenzt (5–25 °C laut Ticket 01). Die Schrittweite ist 1 °C (Spec, Further Notes). Vorhandene halbe Werte werden angezeigt, −/+ rundet auf ganze Grad
- [ ] `TEMPERATURE_STEP` ist 1 °C: Einrichtungs- und Optionsdialog sowie `target_temperature_step` des Raum-Thermostats arbeiten in ganzen Grad
- [ ] Die Vorlaufzeit lässt sich in 15-Minuten-Schritten von 0 bis 3 Stunden einstellen
- [ ] Ist Nacht oder Eco wärmer als Komfort, zeigt das Panel einen Hinweis („Nacht ist wärmer als Komfort – gewollt?“), speichert aber trotzdem. Nacht wärmer als Eco bekommt keinen Hinweis
- [ ] Änderungen erscheinen danach auch im Optionsdialog der Integration
- [ ] Änderungen wirken sofort auf die Solltemperatur des Raums
- [ ] Tests im Test-Home-Assistant decken die Panel API ab, das Panel ist per Checkliste abgenommen

## Comments

**Rückmeldung aus Ticket 16 (25.11.2026):** Frage 9. Ob Stufen und Vorlaufzeit einen eigenen Reiter „Stufen“ bekommen oder auf der Raumseite unter „Räume“ stehen (globale Temperaturen dann unter „Haus“), ist noch offen (Ticket 16, Frage 12). Der Umfang dieses Tickets ändert sich dadurch nicht.
