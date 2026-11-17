# 08: Drehknopf erkennen

Spec: `.scratch/heating-control/spec.md`

**What to build:** Dreht jemand am Knopf eines TRV, wird das als externe Änderung erkannt und genauso behandelt wie eine Übersteuerung über das Raum-Thermostat: Der Raum geht auf Heizen, die Rückfallregel gilt. Die eigenen Befehle der Integration und ihre Echos werden **nie** als Übersteuerung erkannt, auch nicht, wenn jemand kurz nach einem Befehl dreht. Mehrere schnelle Drehschritte ergeben eine einzige Übersteuerung mit dem Endwert. Die Parameter (Echo-Fenster, Entprellung) stammen aus dem Messprotokoll in Ticket 01, und die simulierten TRVs der Tests bilden das gemessene Verhalten nach.

**Blocked by:** 01, 06

**Status:** ready-for-agent

- [ ] Eine Temperaturänderung am TRV ohne vorangehenden eigenen Befehl erzeugt eine Übersteuerung mit diesem Wert
- [ ] Das Echo eines eigenen Befehls (Werte und Zeitverhalten laut Ticket 01) erzeugt keine Übersteuerung
- [ ] Eine Drehung, die innerhalb von 5 s nach einem eigenen Befehl mit abweichendem Wert eintrifft, wird als externe Änderung erkannt
- [ ] Mehrere schnelle Drehschritte ergeben genau eine Übersteuerung mit dem Endwert
- [ ] Ein Zurückspringen des TRV auf `off` nach einem eigenen Befehl gilt nicht als „jemand hat ausgeschaltet“
- [ ] Die simulierten TRVs sind an das gemessene Echo- und Zeitverhalten angepasst
- [ ] Szenario-Tests decken Drehen, Echo, Drehen direkt nach Befehl und schnelles Mehrfachdrehen ab
