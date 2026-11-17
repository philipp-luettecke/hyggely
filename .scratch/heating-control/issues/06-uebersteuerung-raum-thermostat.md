# 06: Übersteuerung über das Raum-Thermostat

Spec: `.scratch/heating-control/spec.md`

**What to build:** Jemand ändert die Temperatur des Raum-Thermostats per Siri (HomeKit-Bridge), in der HA-App oder in Apple Home. Daraufhin schaltet der Raum sichtbar auf Heizen, und diese Temperatur gilt bis zum Rückfall. Die Rückfallregel ist global einstellbar und pro Raum überschreibbar: nächster Schaltpunkt, feste Dauer oder das frühere von beiden (Standard: früheres, 3 h). „Auto“ beendet die Übersteuerung sofort. Heizen ohne Temperatur übersteuert mit dem aktuellen Sollwert. Eine laufende Übersteuerung übersteht samt Restzeit einen Neustart von Home Assistant. Der Grund-Sensor zeigt z. B. „Heizen bis 14:00 (manuell)“.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] `set_temperature` am Raum-Thermostat setzt den Modus auf `heat` und sendet die Temperatur an das TRV
- [ ] Rückfall `earliest` endet am früheren von nächstem Schaltpunkt und Dauer, `next_block` und `duration` entsprechend
- [ ] Eine abweichende Rückfallregel pro Raum hat Vorrang vor der globalen
- [ ] Der Rückfallzeitpunkt ist als Attribut sichtbar
- [ ] `set_hvac_mode(auto)` beendet die Übersteuerung sofort, und die Zeitplan-Stufe gilt wieder
- [ ] `set_hvac_mode(heat)` ohne Temperatur übersteuert mit dem aktuellen Sollwert
- [ ] Eine erneute Temperaturänderung während einer Übersteuerung aktualisiert Temperatur und Rückfallzeitpunkt
- [ ] Nach einem Neustart von Home Assistant sind Übersteuerung und Rückfallzeitpunkt unverändert
- [ ] Der Grund-Sensor zeigt Übersteuerung und Ende
- [ ] Szenario-Tests decken alle drei Rückfallregeln, den Neustart und das Beenden per Auto ab
