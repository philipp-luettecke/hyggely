# 06: Übersteuerung über das Raum-Thermostat

Spec: `.scratch/heating-control/spec.md`

**What to build:** Jemand ändert die Temperatur des Raum-Thermostats per Siri (HomeKit-Bridge), in der HA-App oder in Apple Home. Daraufhin schaltet der Raum sichtbar auf Heizen, und diese Temperatur gilt bis zum Rückfall. Die Rückfallregel ist global einstellbar und pro Raum überschreibbar: nächster Schaltpunkt, feste Dauer oder das frühere von beiden (Standard: früheres, 3 h). „Auto“ beendet die Übersteuerung sofort. Heizen ohne Temperatur übersteuert mit dem aktuellen Sollwert. Eine laufende Übersteuerung übersteht samt Restzeit einen Neustart von Home Assistant. Der Grund-Sensor zeigt z. B. „Heizen bis 14:00 (manuell)“.

**Blocked by:** 03

**Status:** done

- [ ] `set_temperature` am Raum-Thermostat setzt den Modus auf `heat` und sendet die Temperatur an das TRV
- [ ] Rückfall `earliest` endet am früheren von nächstem Schaltpunkt und Dauer, `next_block` und `duration` entsprechend
- [ ] Eine abweichende Rückfallregel pro Raum hat Vorrang vor der globalen
- [ ] Der Rückfallzeitpunkt ist als Attribut sichtbar
- [ ] `set_hvac_mode(auto)` beendet die Übersteuerung sofort, und die Zeitplan-Stufe gilt wieder
- [ ] `set_hvac_mode(heat)` ohne Temperatur übersteuert mit dem aktuellen Sollwert
- [ ] Eine erneute Temperaturänderung während einer Übersteuerung aktualisiert Temperatur und Rückfallzeitpunkt
- [ ] Nach einem Neustart von Home Assistant sind Übersteuerung und Rückfallzeitpunkt unverändert
- [ ] Ist der Rückfallzeitpunkt während des Neustarts verstrichen, steht der Raum nach dem Start sofort auf Auto
- [ ] Der Grund-Sensor zeigt Übersteuerung und Ende
- [ ] Szenario-Tests decken alle drei Rückfallregeln, den Neustart und das Beenden per Auto ab

## Comments

**Rückfallzeitpunkt:** Er wird beim Start der Übersteuerung einmal festgelegt (`target_resolver.mode_expires_at`, rein, ohne HA) und danach nicht mehr verschoben, auch wenn sich der Zeitplan ändert. Eine neue Temperatur oder erneut `heat` startet die Übersteuerung neu, mit neuem Rückfallzeitpunkt. `next_block` nutzt den nächsten Schaltpunkt aus dem Schedule Reader, seit Ticket 04 also mit Vorlaufzeit. Gibt es keinen nächsten Schaltpunkt (leerer Zeitplan), endet `next_block` nie und `earliest` nach der Dauer. Aus endet unabhängig von der Rückfallregel immer am nächsten Schaltpunkt.

**Rückfallregel pro Raum:** Im Raum-Dialog gibt es „Rückfall“ mit der zusätzlichen Auswahl „Globale Einstellung“ (Wert `global`, Standard) und eine optionale „Dauer der Übersteuerung“. Die Regel des Raums gilt, wenn sie nicht `global` ist. Die Dauer des Raums gilt, sobald sie gesetzt ist, auch bei globaler Regel (z. B. Bad: global `earliest`, aber nur 1 h). Leere Dauer heißt globale Dauer. Räume ohne diese Felder folgen der globalen Einstellung.

**Attribute des Raum-Thermostats:** `override_expiry` (`datetime`, Rückfallzeitpunkt bei Heizen und Aus, sonst `None`) und `reason` (Grund-Code aus dem Target Resolver, z. B. `override`, `schedule`). Für den Grund-Sensor aus Ticket 05 liefert der Resolver bei Übersteuerung `Reason(code=override, params={"until": <Rückfallzeitpunkt>})`; daraus wird „Heizen bis 14:00 (manuell)“. Nach dem Merge von 05 prüft `test_override.py` den Klartext „Heizen bis 14:00 (manuell)“ am Grund-Sensor und dessen Rückfallzeitpunkt nach einem Neustart. Das Attribut `reason` am Raum-Thermostat trägt den Grund-Code aus 05 (z. B. `override`, `eco`).

**Zusammenspiel mit Ticket 13:** Der gespeicherte Stand wird geladen, bevor der Controller startet. Die gestaffelten Befehle beim Start von Home Assistant senden deshalb schon die wiederhergestellte Übersteuerung (Test `test_override_restored_while_home_assistant_starts_reaches_the_trv`).

**Speicherung über Neustart und Neuladen:** `room_mode_store.py` speichert Raum-Modus, Übersteuerungstemperatur und Rückfallzeitpunkt aller Räume in einem `Store` (`.storage/climate_control.<entry_id>.room_modes`). Jede Änderung wird sofort geschrieben, nicht erst beim Entladen. So hängt nichts davon ab, wie Home Assistant herunterfährt (auch ein Absturz verliert nichts). Beim Start lädt der Controller seinen Stand; ist der Rückfallzeitpunkt verstrichen, entscheidet der Resolver sofort Auto. Gelöschte Räume fallen beim nächsten Laden heraus, beim Entfernen der Integration wird die Datei gelöscht. `RestoreEntity` habe ich bewusst nicht genommen: Der Zustand gehört dem Room Controller, nicht der Entität, und die Entität bleibt dünn.

**Aus (für Ticket 07):** Aus läuft über denselben Mechanismus, wird also schon gespeichert und nach einem Neustart bis zum nächsten Schaltpunkt wiederhergestellt. Tests dafür und den Grund „Aus bis …“ ergänzt Ticket 07. `test_room_modes.py` enthält nur noch den Aus-Test aus 03; die Übersteuerungs-Tests stehen in `tests/test_override.py`.

**Tests:** `scenario.shut_down()`/`start_up()` simulieren den Neustart (Eintrag entladen, Zeit vorspulen, neu einrichten). Dabei bleibt nur der Speicher erhalten. `living_room()` nimmt `global_settings`, `add_main_entry()` beliebige globale Einstellungen, und `LivingRoom.call()` ruft eine `climate`-Aktion am Raum-Thermostat auf.

**Nachtrag (Review): `set_temperature` mit `hvac_mode`.** HA 2026.11 reicht ein mitgeschicktes `hvac_mode` unverändert an `async_set_temperature` weiter (ohne Prüfung gegen die angebotenen Modi). Bisher wurde es verworfen. Jetzt gilt: `off` schaltet den Raum aus (wie `set_hvac_mode(off)`, bis zum nächsten Schaltpunkt), `auto` kehrt sofort zum Zeitplan zurück; die Temperatur wird in beiden Fällen ignoriert. `heat`, kein Modus oder ein nicht angebotener Modus übersteuern wie bisher mit der Temperatur. Tests in `tests/test_override.py`.

**Abgeschlossen:** Merge-Commit `1b049d5` auf `feat/heating-control`. Ergebnis: Übersteuerung über das Raum-Thermostat mit Rückfallregeln `next_block`/`duration`/`earliest` (global und pro Raum), Rückfallzeitpunkt als Attribut, Wiederherstellung nach Neustart; 98 Tests grün.
