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

## Comments

**Bestand:** Aus war aus 03/05/06 weitgehend vorhanden: Resolver-Regel `room_off` mit `until` = Rückfallzeitpunkt, `mode_expires_at` setzt bei Aus immer den nächsten Schaltpunkt (ohne Rückfallregel), Speicherung über `room_mode_store.py`. Ergänzt wurden die Szenario-Tests in `tests/test_room_modes.py`: Aus und Rückkehr am Schaltpunkt, „Aus bis 17:00“, Rückfallregel `duration` 1 h gilt nicht, Temperatur während Aus startet eine Übersteuerung mit eigener Rückfallregel (3 h), Auto beendet Aus sofort, Neustart (bleibt aus, Schaltpunkt während des Neustarts verstrichen, gestaffelter Start schaltet ein zwischenzeitlich heizendes TRV wieder aus).

**Entscheidung: Heizen ohne Temperatur während Aus.** Die Spec sagt, `set_hvac_mode(heat)` übersteuert mit dem aktuellen Sollwert. Während Aus wäre das der Frostschutz (7 °C), also eine 3-stündige „Übersteuerung“ auf 7 °C, sobald jemand in Apple Home von Aus auf Heizen tippt. Umgesetzt ist stattdessen: Heizen aus Aus übersteuert mit dem Sollwert, den Auto jetzt hätte (Zeitplan-Stufe bzw. Abwesend). Das ist die reine Funktion `target_resolver.heat_temperature`. Ticket 10 sollte prüfen, ob „Fenster offen“ (ebenfalls Frostschutz) dieselbe Behandlung braucht.

**Für Ticket 08:** Ausschalten am Gerät läuft über `RoomController.async_set_room_mode(RoomMode.OFF)`, denselben Einstieg wie Aus am Raum-Thermostat. Der Rückfallzeitpunkt ist dann automatisch der nächste Schaltpunkt.

**Randfälle (bewusst wie bei der Übersteuerung in 06):** Der Rückfallzeitpunkt von Aus wird beim Ausschalten festgelegt und bei einer späteren Zeitplanänderung nicht verschoben. Ein Zeitplan ganz ohne Blöcke hat keinen Schaltpunkt; dann bleibt Aus bis „Auto“ bestehen. Mit Vorlaufzeit endet Aus am wirksamen Schaltpunkt, also um die Vorlaufzeit vor Blockbeginn.
