# 09: Mehrere Thermostate in einem Raum

Spec: `.scratch/heating-control/spec.md`

**What to build:** Ein Raum kann mehrere TRVs haben. Alle erhalten immer denselben Sollwert und Modus. Die Ist-Temperatur des Raum-Thermostats ist der Mittelwert der verfügbaren TRVs. Dreht jemand an einem TRV, gilt die Übersteuerung für den ganzen Raum, und die übrigen TRVs werden angeglichen, ohne dass dies erneut als externe Änderung erkannt wird. Ein nicht erreichbares TRV zählt nicht zum Mittelwert.

**Blocked by:** 08

**Status:** ready-for-agent

- [ ] Im Einrichtungs- und Optionsdialog eines Raums lassen sich mehrere TRVs wählen
- [ ] Alle TRVs eines Raums erhalten bei jeder Entscheidung denselben Sollwert und Modus
- [ ] Die Ist-Temperatur ist der Mittelwert der verfügbaren TRVs, nicht erreichbare werden ignoriert
- [ ] Eine Drehung an einem TRV erzeugt eine Übersteuerung des Raums und gleicht die anderen TRVs an
- [ ] Das Angleichen erzeugt keine weitere Übersteuerung
- [ ] Szenario-Tests mit zwei simulierten TRVs decken Mittelwert, Angleichen und ein nicht erreichbares TRV ab
