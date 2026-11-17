# 01: Messprotokoll an der tado-Hardware

Spec: `.scratch/heating-control/spec.md`

**What to build:** Ein ausgefülltes Messprotokoll, das beschreibt, wie sich die echten tado-TRVs über HomeKit in Home Assistant verhalten. Es legt die Parameter des Override Detector fest und dient als Vorlage für die simulierten TRVs in den Tests.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

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

## Ergebnis A

_(Attribute einfügen, Batterie ja/nein)_

## Ergebnis B

| Versuch | Sekunden | Bemerkung |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| Schnelles Drehen | Anzahl Ereignisse: | Werte: |

## Ergebnis C

_(Ereignisse mit Zeitpunkt, Temperatur, Zustand, context.id)_

## Ergebnis D

_(ohne hvac_mode / mit hvac_mode)_

## Ergebnis E

_(Zeitpunkte und Beobachtungen)_

## Acceptance criteria

- [ ] Ergebnisse A bis E sind ausgefüllt
- [ ] Es ist eindeutig festgehalten, ob tado über HomeKit einen Batteriestand liefert
- [ ] Mindestens ein vollständiger `state_changed`-Eintrag für eine Drehung am Knopf und einer für einen Befehl aus Home Assistant ist enthalten
- [ ] Das Zurückspringen auf „Aus“ (Messung D) ist bestätigt oder widerlegt
