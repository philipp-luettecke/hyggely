# 12: Hausbetriebsart und Urlaub mit Enddatum

Spec: `.scratch/heating-control/spec.md`

**What to build:** Eine globale Auswahl-Entität „Hausbetriebsart“ bietet Automatik, Urlaub und Aus. Zusätzlich gibt es eine Datum-Uhrzeit-Entität „Urlaubsende“. Bei Urlaub erhalten alle Räume die Urlaubstemperatur. Ist das Urlaubsende erreicht, wechselt die Hausbetriebsart automatisch auf Automatik. Bei Aus erhalten alle Räume Frostschutz. Eine Übersteuerung schlägt Urlaub, Aus und Abwesend. Das Fenster schlägt alles. Beide Entitäten überstehen einen Neustart und lassen sich per Siri oder Automation steuern. Damit ist die vollständige Rangfolge aus der Spec umgesetzt.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Die Hausbetriebsart ist als Auswahl-Entität mit Automatik, Urlaub und Aus verfügbar
- [ ] Das Urlaubsende ist als Datum-Uhrzeit-Entität verfügbar. Bei Erreichen wechselt die Hausbetriebsart auf Automatik
- [ ] Bei Urlaub gilt die Urlaubstemperatur in allen Räumen ohne Übersteuerung
- [ ] Bei Aus gilt Frostschutz in allen Räumen ohne Übersteuerung
- [ ] Eine Übersteuerung wirkt auch bei Urlaub, Aus und Abwesend
- [ ] Hausbetriebsart und Urlaubsende überstehen einen Neustart
- [ ] Der Grund-Sensor zeigt Urlaub (mit Ende) bzw. „Haus aus“
- [ ] Szenario-Tests decken die vollständige Rangfolge Fenster > Aus > Übersteuerung > Haus aus > Urlaub > Abwesend > Zeitplan ab
