# 08: Drehknopf erkennen

Spec: `.scratch/heating-control/spec.md`

**What to build:** Dreht jemand am Knopf eines TRV, wird das als externe Änderung erkannt und genauso behandelt wie eine Übersteuerung über das Raum-Thermostat: Der Raum geht auf Heizen, und die Rückfallregel gilt. Eigene Befehle der Integration werden **nie** als Übersteuerung erkannt.

Grundlage ist das Messprotokoll in Ticket 01:
- Ein eigener Befehl erscheint sofort (< 0,2 s) im Zustand des TRV, mit dem eigenen Context. Spätere Echos gibt es nicht.
- Eine Drehung am Knopf kommt erst bei der nächsten Minutenabfrage von Home Assistant an (bis ca. 61 s später). Sie hat einen neuen Context ohne `user_id`/`parent_id` und enthält nur den Endwert, auch bei mehreren schnellen Rasten.

Daraus folgt die Regel:
- Eine Änderung der Solltemperatur oder des Modus des TRV, die nicht dem zuletzt gesendeten Sollzustand entspricht, ist eine externe Änderung.
- **Unklarer Fall:** Zeigt die erste Abfrage nach einem eigenen Befehl wieder exakt den Zustand **vor** dem Befehl, gilt der Befehl als nicht übernommen. Dann wird einmal erneut gesendet, statt eine Übersteuerung anzunehmen.
- Wird das TRV am Gerät ausgeschaltet, ist das ebenfalls eine externe Änderung. Sie wird wie Aus am Raum-Thermostat behandelt, also bis zum nächsten Schaltpunkt.
- Werte, die das TRV im Modus `off` meldet (`temperature: null`, min/max 7/35), und ein kurzzeitig gemeldeter Modus `None` sind keine Änderungen.

Die simulierten TRVs der Tests bilden dieses Verhalten nach: Sie übernehmen einen Befehl sofort, melden Drehungen erst beim nächsten Abfragetakt und ignorieren eine Temperatur ohne Modus, solange sie aus sind.

**Blocked by:** 01, 06

**Status:** ready-for-agent

- [ ] Eine Temperaturänderung am TRV, die vom zuletzt gesendeten Wert abweicht, erzeugt eine Übersteuerung mit diesem Wert
- [ ] Der sofortige Zustand nach einem eigenen Befehl erzeugt keine Übersteuerung
- [ ] Zeigt die erste Abfrage nach einem eigenen Befehl den Zustand vor dem Befehl, wird genau einmal erneut gesendet und keine Übersteuerung erzeugt
- [ ] Ausschalten am Gerät setzt den Raum auf Aus bis zum nächsten Schaltpunkt
- [ ] `temperature: null`, die Bereichswerte im Modus `off` und ein Modus `None` lösen nichts aus
- [ ] Die simulierten TRVs bilden Abfragetakt, sofortige Übernahme eigener Befehle und das Ignorieren einer Temperatur ohne Modus nach
- [ ] Szenario-Tests decken Drehen, eigenen Befehl, nicht übernommenen Befehl, Ausschalten am Gerät und ungültige Werte ab

## Comments

**Module:**
- `override_detector.py` (`OverrideDetector`, einer pro Raum, ohne HA-Abhängigkeit): vergleicht die gemeldete Einstellung eines TRV (`TrvSetting`: Modus, Temperatur; bei `off` nur der Modus) mit dem Sollzustand der aktuellen Entscheidung des Raums. Gleich heißt Echo oder nichts Neues (`MATCHES`), sonst externe Änderung. Ausnahme: Zeigt die erste Abfrage nach einem eigenen Befehl exakt die Einstellung von **vor** dem Befehl, ist das `NOT_TAKEN` (einmal erneut senden), beim wiederholten Befehl `NOT_TAKEN_AGAIN` (nichts tun).
- `TrvReachability` hat einen neuen Callback `on_report`: Er bekommt nur Zustände der `climate`-Entität von TRVs, die vorher **und** jetzt Befehle annehmen. Eingefrorene Werte, der Modus `None` und die Rückkehr nach einem Ausfall erreichen den Detector daher nie (Ticket 13 sendet dann wie bisher den Sollzustand erneut).
- `RoomController`: Jeder Befehl wird mit der Einstellung davor beim Detector notiert. Externe Änderung mit Modus `off` → `async_set_room_mode(OFF)` (bis zum nächsten Schaltpunkt, wie Aus am Raum-Thermostat), sonst `async_set_override(temperatur)`. Drehen bei ausgeschaltetem Raum übersteuert also mit dem Wert am Knopf.

**Entscheidung: „erste Abfrage“ über die Zeit.** Ein übernommener Befehl erzeugt bei der nächsten Abfrage keine Zustandsänderung, die erste Abfrage ist also nicht direkt beobachtbar. Als erste Abfrage gilt deshalb eine Meldung bis `FIRST_POLL_WITHIN` = 62 s nach dem Befehl (Minutentakt, gemessen bis ca. 61 s). Eine spätere Meldung mit dem alten Wert ist eine Drehung am Knopf (Test „zurückgedreht nach der ersten Abfrage“). Das ist kein Echo-Fenster: Echos werden weiterhin nur über den Vergleich erkannt.

**Entscheidung: zweimal nicht übernommen.** Zeigt auch die erste Abfrage nach dem wiederholten Befehl wieder den alten Wert, wird nicht ein drittes Mal gesendet und keine Übersteuerung angenommen. Der Raum behält seinen Sollwert, das TRV weicht ab, bis die nächste Entscheidung (z. B. Schaltpunkt) ohnehin neu sendet. Ein Logbuch-/Reparaturhinweis dafür ist nicht umgesetzt.

**Vergleich mit der Entscheidung statt mit dem „zuletzt gesendeten“ Wert:** Jedes erreichbare TRV hat nach einer Entscheidung entweder den Befehl bekommen oder hatte den Sollzustand schon. Der Sollzustand der Entscheidung ist daher der zuletzt gesendete bzw. bestätigte Zustand, auch direkt nach dem Start ohne eigenen Befehl. Für Ticket 09 heißt das: Angleichen der übrigen TRVs erzeugt Echos mit dem neuen Sollwert und damit keine weitere Übersteuerung. Der Detector merkt sich Befehle bereits pro TRV.

**Für Ticket 10:** Eine Drehung bei offenem Fenster wird hier zur Übersteuerung (gemerkt), die Entscheidung bleibt Frostschutz, und das TRV erhält wieder `off`. Ob das so gewünscht ist, gehört zu 10.

**Simulierte TRVs:** `turn_knob(t)` und `switch_off()` wirken sofort im Gerät, Home Assistant sieht sie erst bei der nächsten vollen Minute, nur mit dem Endwert und neuem Context. `commands_to_lose = n`: Die nächsten n Befehle zeigt HA sofort, das Gerät übernimmt sie nicht, und die nächste Abfrage meldet wieder die alten Werte. Ein ausgeschaltetes TRV ignoriert `set_temperature` ohne `hvac_mode`. `report()` meldet weiterhin sofort (z. B. Ist-Temperatur) und gilt im laufenden Betrieb bei abweichendem Sollwert als externe Änderung. `test_trv_already_at_target_gets_no_command` nutzt deshalb jetzt eine Drehung am Knopf. Hinweis für Tests: Vor einer Drehung mit `clock.advance_to` (nicht `clock.set`) an die Uhrzeit gehen, sonst holt der überfällige Abfragetakt die Drehung zu früh ab.

**Offen (Spec):** Falls das TRV per Befehl gesetzte halbe Grad im Echo rundet (Schrittweite ungeklärt), würde das als externe Änderung erkannt. Mit der Klärung der Schrittweite prüfen.
