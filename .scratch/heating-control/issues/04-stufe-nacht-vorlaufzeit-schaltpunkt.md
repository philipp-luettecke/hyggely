# 04 – Stufe Nacht, Vorlaufzeit und nächster Schaltpunkt

Status: ready-for-agent
Blocked by: 03
Spec: `.scratch/heating-control/spec.md`

## What to build

Blöcke im Zeitplan tragen eine **Stufe**:

- Die Stufe steht in den Zusatzdaten des Blocks unter dem Schlüssel `level` (`comfort` oder `night`).
- Ein Block ohne Angabe gilt als Komfort. Außerhalb von Blöcken gilt Eco.
- Der Admin legt pro Raum zusätzlich die Nacht-Temperatur und eine **Vorlaufzeit** fest.

Der Raum wendet die Stufe eines Blocks bereits um die Vorlaufzeit vor dessen Beginn an. So ist das Bad morgens warm, wenn der Komfort-Block beginnt.

Der **Schedule Reader** berechnet den **nächsten Schaltpunkt**, also den nächsten Wechsel der wirksamen Stufe einschließlich der Vorlaufzeit. Der Room Controller bewertet zu diesem Zeitpunkt neu. Das Raum-Thermostat zeigt die aktive Stufe als Attribut an.

## Acceptance criteria

- [ ] Block mit `level: night` → Nacht-Temperatur; Block ohne `level` → Komfort; kein Block → Eco
- [ ] Zwei direkt aneinandergrenzende Blöcke mit unterschiedlicher Stufe schalten genau an der Grenze um
- [ ] Mit Vorlaufzeit 30 min gilt die Komforttemperatur ab 06:00, wenn der Komfort-Block um 06:30 beginnt
- [ ] Die Vorlaufzeit wirkt nur auf den Beginn eines Blocks; beim Blockende wird nicht vorzeitig abgesenkt
- [ ] Wird der Zeitplan geändert, berechnet sich der nächste Schaltpunkt neu
- [ ] Das Raum-Thermostat zeigt die aktive Stufe als Attribut an
- [ ] Szenario-Tests mit vorgespulter Zeit decken alle Kriterien ab, auch den Wochenwechsel von Sonntag auf Montag

## Blocked by

- 03 – Ein Raum folgt dem Zeitplan
