# 01: Messprotokoll an der tado-Hardware

Spec: `.scratch/heating-control/spec.md`

**What to build:** Ein ausgefülltes Messprotokoll, das beschreibt, wie sich die echten tado-TRVs über HomeKit in Home Assistant verhalten. Es legt die Parameter des Override Detector fest und dient als Vorlage für die simulierten TRVs in den Tests.

**Blocked by:** None (can start immediately)

**Status:** done

## Vorbereitung

- Wähle **ein** TRV in einem Raum, in dem du ungestört drehen kannst. Notiere seine Entity-ID (`climate.…`).
- Öffne in Home Assistant **Entwicklerwerkzeuge → Zustände** und filtere auf diese Entity-ID.
- Öffne in einem zweiten Tab **Entwicklerwerkzeuge → Ereignisse**, trage unter „Ereignis abonnieren“ `state_changed` ein und klicke auf „Abonnieren“. Jede Zustandsänderung erscheint dort mit Zeitstempel und `context`.
- Halte eine Stoppuhr bereit (Handy).

## Messung A: Eigenschaften der Entität

Kopiere aus **Entwicklerwerkzeuge → Zustände** alle Attribute des TRV in den Abschnitt „Ergebnis A“. Mich interessieren besonders `hvac_modes`, `min_temp`, `max_temp`, `target_temp_step`, `current_temperature`, `current_humidity` und `hvac_action`.

Prüfe außerdem unter **Einstellungen → Geräte & Dienste → HomeKit-Gerät → (das TRV)**, welche Entitäten das Gerät hat. Gibt es etwas mit Batterie (`sensor.…battery` oder `binary_sensor.…battery`)?

## Messung B: Zeit von einer Drehung am Knopf bis zur Zustandsänderung in Home Assistant (5×)

1. Starte die Stoppuhr in dem Moment, in dem du am TRV um **einen** Schritt drehst.
2. Stoppe, sobald im Ereignis-Tab ein `state_changed` für das TRV mit der neuen Temperatur erscheint.
3. Trage die Sekunden ein. Warte vor dem nächsten Versuch 1 Minute.
4. Notiere bei mindestens einem Versuch den kompletten Ereignis-Eintrag (inklusive `context` mit `id`, `parent_id`, `user_id`).

Dreh außerdem einmal **schnell mehrere Schritte** hintereinander (z. B. 4× in 3 s) und notiere, wie viele `state_changed`-Ereignisse ankommen und mit welchen Werten.

## Messung C: Echo nach einem Befehl aus Home Assistant

1. **Entwicklerwerkzeuge → Aktionen** → `climate.set_temperature`, Ziel: das TRV, `temperature`: 1 °C über dem aktuellen Wert, `hvac_mode: heat`. Ausführen.
2. Notiere aus dem Ereignis-Tab **alle** `state_changed` des TRV in den nächsten 30 s: Zeitpunkt relativ zum Ausführen, `temperature`, Zustand (`heat`/`off`) und `context.id`.
3. Führe die Aktion zweimal aus.

## Messung D: Temperatur setzen, während das TRV auf „Aus“ steht

1. Setze das TRV per `climate.set_hvac_mode` auf `off`. Warte 30 s.
2. Rufe `climate.set_temperature` mit einer Temperatur, aber **ohne** `hvac_mode` auf.
3. Notiere alle `state_changed` in den nächsten 30 s. Springt der Zustand auf `heat` und nach einigen Sekunden zurück auf `off`?
4. Wiederhole das Ganze mit `hvac_mode: heat` im selben Aufruf.

## Messung E: Bridge kurz stromlos

1. Ziehe den Stecker der tado-Bridge für 60 s, dann wieder einstecken.
2. Notiere: Wann wird das TRV in Home Assistant `unavailable`? Wann ist es wieder verfügbar? Welche Werte hat es danach (Temperatur, Modus)? Musstest du etwas neu laden?

Durchgeführt am 2026-11-17 mit Claude über Home Assistant MCP. Die Werte wurden aus der Übermittlung übernommen. Wo Text bei der Übertragung verstümmelt war, sind die Sekunden aus den Zeitstempeln nachgerechnet und als „(berechnet)“ markiert.

## Ergebnis A

Entity-ID: `climate.tado_smart_radiator_thermostat_va3404008704` („tado Thermostat Arbeitszimmer“, tado SRT01, FW 215.1, `homekit_controller` über die Bridge)

- `hvac_modes`: `["off", "heat"]`, kein `auto`
- `min_temp` 5 / `max_temp` 25. **Im Modus `off` meldet HA abweichend 7 / 35.**
- `target_temp_step`: Attribut nicht vorhanden. Gemessen: 1 Raste am Knopf = 1 °C
- `temperature`: 22, **im Modus `off`: `null`**
- `current_temperature`: 22
- `current_humidity`: 54
- `hvac_action`: `idle`/`heating`
- `supported_features`: 385 (TARGET_TEMPERATURE + TURN_OFF + TURN_ON)
- Entitäten des Geräts: `climate.…`, `sensor.…_current_temperature`, `sensor.…_current_humidity`, `select.…_temperature_display_units`, `button.…_identify`

Batterie verfügbar: **nein** (keine Batterie-Entität, auch nicht deaktiviert oder versteckt)

## Ergebnis B

| Durchgang | Gedreht um | In HA angekommen | Sekunden | Bemerkung |
|---|---|---|---|---|
| 1 | 11:33:00 | 11:34:00.226 | 60,2 (berechnet) | 1 Raste, kein Zwischenwert |
| 2 | 11:36:00 | 11:37:00.241 | 60,2 | 1 Raste ↓, 23 → 22 °C |
| 3 | 11:58:30 | 11:59:00.256 | 30,3 (berechnet) | 1 Raste |
| 4 | 12:05:22 | 12:06:00.237 | 37,8 | 1 Raste ↓, 23 → 22 °C |
| 5 | 12:39:11 | 12:40:00.275 | 49,3 (berechnet) | 1 Raste |
| Schnelles Drehen | 12:42:10–12:42:13 | 12:43:01.373 | 48,4 ab Ende / 51,4 ab Beginn | Anzahl Änderungen: 1, Werte: 23 → 19 °C, keine Zwischenschritte |

- Alle Änderungen kamen jeweils zu Beginn der nächsten vollen Minute an (Sekunde :00,2 bis :01,4).
- Das Log meldet: „This device does not support push, so only polling operations will be supported“. **Home Assistant fragt das Gerät nur einmal pro Minute ab.**

Context einer Drehung am Knopf: neue `id` je Änderung, `parent_id` und `user_id` bei allen 6 Drehungen `null`.

## Ergebnis C

| Durchgang | Zeit ab Aufruf (s) | Solltemperatur | Zustand | Bemerkung |
|---|---|---|---|---|
| 1 | 0 | 19 | heat | Aufruf `set_temperature` 20 + `hvac_mode: heat` |
| 1 | +0,08 | 20 | heat | Context des Aufrufers (`user_id` gesetzt) |
| 1 | bis +85 | – | – | keine weitere Änderung, auch nicht bei der nächsten Abfrage |
| 2 | 0 | 20 | heat | Aufruf `set_temperature` 21 + `hvac_mode: heat` |
| 2 | +0,07 | 21 | heat | Context des Aufrufers |
| 2 | bis +87 | – | – | keine weitere Änderung, kein Echo |

Keine Zwischenwerte, kein alter Wert, kein Hin- und Herspringen.

## Ergebnis D

Ohne `hvac_mode`:
- `set_hvac_mode off`: Zustand `off`, Solltemperatur `null`, min/max 7/35, stabil
- `set_temperature 21` ohne `hvac_mode`: **Der Aufruf wird ohne Fehler angenommen, bewirkt aber nichts.** Das TRV bleibt 90 s lang `off`, kein Wechsel auf `heat` und damit auch kein Zurückspringen.
- Ob das Gerät 21 °C intern gespeichert hat, ist über MCP nicht ermittelbar.

Mit `hvac_mode: heat`:
- `set_temperature 22` mit `hvac_mode: heat`: nach +0,10 s `heat`, 22 °C, min/max wieder 5/25, stabil über 86 s

## Ergebnis E

- 13:52:25 Stecker gezogen
- **Die `climate`-Entität wurde nie `unavailable` oder `unknown`.** Sie blieb mit den alten Werten stehen.
- Nur `sensor.…_current_temperature` war ab 13:54:01 `unavailable`, ca. 96 s nach dem Ziehen.
- 13:53:32 wieder eingesteckt
- 13:53:40 Verbindung zur Bridge neu aufgebaut (Log)
- 13:55:00 Temperatursensor wieder verfügbar
- 13:57:00 `climate`-Entität wieder aktuell, 3 min 28 s nach dem Einstecken

Zwischenzustand:
- Um 13:55:00 lieferte die Bridge für den Modus `None`. Das Schreiben des `climate`-Zustands brach mit einem Fehler in `homekit_controller` ab.
- Die `climate`-Entität zeigte deshalb noch den alten Wert 22,7 °C, während der Sensor schon 22,6 °C meldete.
- Die Luftfeuchte zeigte kurz 52 statt 54 %.

Zustand danach: `heat`, 22 °C, unverändert wie vorher. Neu laden nötig: nein.

## Kurzfassung

1. Längste Verzögerung von einer Drehung am Knopf bis zu HA: 60,2 s. Ursache ist die Abfrage im Minutentakt ohne Push, das theoretische Maximum liegt bei ca. 61 s.
2. Beim schnellen Drehen kommt nur der Endwert an (4 Rasten ergeben 1 Änderung).
3. Echos nach eigenem Befehl: 0. HA schreibt den Zustand sofort nach dem Befehl einmal (nach 0,07–0,10 s, mit Context des Aufrufers), danach nichts mehr.
4. Zurückspringen auf „Aus“: nein. Stattdessen wird `set_temperature` ohne `hvac_mode` an einem ausgeschalteten TRV stillschweigend ignoriert. Mit `hvac_mode: heat` im selben Aufruf funktioniert es.
5. Batteriestand verfügbar: nein.
6. Bei einem Ausfall der Bridge wird die `climate`-Entität **nicht** `unavailable`, sondern friert still ein. Der Temperatursensor des Geräts wird nach ca. 1,5 min `unavailable`. Nach dem Wiedereinstecken ist die `climate`-Entität nach 3 min 28 s wieder aktuell.

## Acceptance criteria

- [x] Ergebnisse A bis E sind ausgefüllt
- [x] Es ist eindeutig festgehalten, ob tado über HomeKit einen Batteriestand liefert
- [x] Mindestens ein vollständiger `state_changed`-Eintrag für eine Drehung am Knopf und einer für einen Befehl aus Home Assistant ist enthalten (Context-Werte aus B und C)
- [x] Das Zurückspringen auf „Aus“ (Messung D) ist bestätigt oder widerlegt (widerlegt)

## Comments

**Folgerungen für die Umsetzung** (in Spec und Tickets 08, 13, 14 und 19 übernommen):

- **Erkennen einer Drehung am Knopf:**
  - Ein eigener Befehl erscheint sofort (< 0,2 s) im Zustand des TRV, mit dem eigenen Context. Spätere Echos gibt es nicht.
  - Eine Drehung am Knopf kommt erst bei der nächsten Minutenabfrage an, mit neuem Context ohne `user_id`/`parent_id` und nur mit dem Endwert.
  - Entprellung oder Echo-Fenster sind daher nicht nötig. Es reicht der Vergleich mit dem zuletzt gesendeten Wert.
- **Unklarer Fall:** Zeigt die erste Abfrage nach einem eigenen Befehl wieder exakt den Wert **vor** dem Befehl, hat das Gerät den Befehl vermutlich nicht übernommen. Dann einmal erneut senden. Jeder andere abweichende Wert ist eine Drehung am Knopf.
- **Immer Modus und Temperatur zusammen senden.** Sonst wird der Befehl an einem ausgeschalteten TRV stillschweigend ignoriert.
- **Im Modus `off` meldet das TRV `temperature: null` und min/max 7/35.** Diese Werte sind keine Änderung und dürfen nicht als Bereich übernommen werden.
- **Ausfall der Bridge:** Die `climate`-Entität friert still ein, statt `unavailable` zu werden. Ein TRV gilt daher als „nicht erreichbar“, wenn seine `climate`-Entität `unavailable` ist **oder** der Temperatursensor desselben Geräts `unavailable` ist. Nach dem Wiedereinstecken kann es über 3 min dauern, bis wieder frische Werte kommen.
- **Ungültiger Modus:** Ein kurzzeitig gemeldeter Modus `None` nach dem Neuverbinden wird ignoriert und nicht als Änderung behandelt.
- **Batterie:** kein Batteriestand, Batterie-Benachrichtigungen entfallen endgültig.
- **Offen: Schrittweite.** Kann man per Befehl auch halbe Grad (z. B. 21,5 °C) setzen? Der Knopf arbeitet in 1-°C-Schritten. Bis zur Klärung arbeitet die Integration mit 0,5 °C und rundet nicht.
