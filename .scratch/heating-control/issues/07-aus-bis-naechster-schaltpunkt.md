# 07: Aus bis zum nächsten Schaltpunkt

Spec: `.scratch/heating-control/spec.md`

**What to build:** Schaltet jemand einen Raum über das Raum-Thermostat aus (Siri, Apple Home, HA), gilt Frostschutz. Das TRV wird auf `off` gesetzt. Beim nächsten Schaltpunkt kehrt der Raum automatisch zu Auto zurück, unabhängig von der Rückfallregel. „Auto“ beendet Aus sofort. Aus übersteht einen Neustart. Der Grund-Sensor zeigt z. B. „Aus bis 17:00“.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] `set_hvac_mode(off)` setzt den Raum auf Aus und das TRV auf `off`
- [ ] Am nächsten Schaltpunkt wechselt der Raum zu Auto und das TRV erhält die Zeitplan-Stufe
- [ ] Die Rückfallregel (Dauer) gilt für Aus nicht
- [ ] Eine Temperaturänderung während Aus startet eine Übersteuerung (Heizen)
- [ ] Nach einem Neustart von Home Assistant bleibt der Raum bis zum nächsten Schaltpunkt aus
- [ ] Szenario-Tests decken Aus, Rückkehr am Schaltpunkt, Wechsel zu Heizen und Neustart ab
