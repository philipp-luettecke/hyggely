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
