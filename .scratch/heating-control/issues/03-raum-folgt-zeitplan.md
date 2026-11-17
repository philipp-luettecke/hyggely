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
