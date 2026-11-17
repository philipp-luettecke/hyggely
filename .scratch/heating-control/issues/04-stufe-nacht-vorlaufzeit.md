# 04: Stufe Nacht, Vorlaufzeit und nächster Schaltpunkt

Spec: `.scratch/heating-control/spec.md`

**What to build:** Blöcke im Zeitplan tragen in ihren Zusatzdaten eine Stufe (`level`: `comfort` oder `night`). Ein Block ohne Angabe gilt als Komfort, außerhalb von Blöcken gilt Eco. Der Raum bekommt zusätzlich eine Temperatur für Nacht und eine Vorlaufzeit. Beginnt ein Block innerhalb der Vorlaufzeit, gilt bereits seine Stufe. Das Bad ist so morgens zum Blockbeginn warm. Das Raum-Thermostat kennt außerdem den nächsten Schaltpunkt als Attribut. Ihn brauchen spätere Tickets für den Rückfall.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Ein Block mit `level: night` setzt die Nacht-Temperatur, ein Block ohne Angabe die Komfort-Temperatur
- [ ] Bei aneinandergrenzenden Blöcken mit unterschiedlicher Stufe wechselt die Solltemperatur genau an der Grenze
- [ ] Mit einer Vorlaufzeit von z. B. 30 min wird die Stufe eines Blocks 30 min vor seinem Beginn angewendet
- [ ] Die Vorlaufzeit wirkt nur auf den Beginn eines Blocks. Beim Blockende wird nicht vorzeitig abgesenkt
- [ ] Der Blockbeginn um Mitternacht, Blöcke über den Tageswechsel und der Wochenwechsel von Sonntag auf Montag verhalten sich korrekt
- [ ] Der nächste Schaltpunkt ist als Attribut verfügbar, berücksichtigt die Vorlaufzeit und wird bei einer Änderung am Zeitplan neu berechnet
- [ ] Das Raum-Thermostat zeigt die aktive Stufe als Attribut
- [ ] Nacht-Temperatur und Vorlaufzeit sind im Optionsdialog des Raums änderbar
- [ ] Szenario-Tests decken Stufen, Vorlaufzeit und Grenzfälle am Tageswechsel ab
