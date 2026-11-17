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

## Comments

**Umsetzung:** Der Raum-Dialog nutzt `multiple=True`; gespeichert wird die Liste unverändert. Ein Raum ohne TRV wird mit dem Fehler `no_trvs` abgewiesen (vorher verhinderte das der Einzel-Selektor). Senden, Angleichen und Erkennung brauchten keine Änderung: Der Override Detector vergleicht jede Meldung mit der aktuellen Entscheidung, das angeglichene TRV meldet also den neuen Sollwert und erzeugt keine weitere Übersteuerung (Test: Rückfallzeit bleibt bei 15:11). Nicht übernommene Befehle, Nachsenden nach Ausfall und Staffelung nach Neustart wirken pro TRV (Tests in `tests/test_several_trvs.py`).

**Ist-Temperatur:** Mittelwert der TRVs, die Befehle annehmen (`TrvReachability.takes_commands`). Damit zählen weder eingefrorene Werte während eines Bridge-Ausfalls noch die Werte im kurzzeitig ungültigen Modus nach der Rückkehr. Das Raum-Thermostat abonniert dafür auch die Temperatursensoren der TRVs. Ohne erreichbares TRV gibt es keine Ist-Temperatur. Gerundet wird von Home Assistant auf Zehntel.

**Entscheidung:** Drehen zwei Personen in derselben Minute an zwei TRVs unterschiedlich, gewinnt die zuletzt verarbeitete Meldung; beide TRVs werden darauf angeglichen. Nicht eigens getestet.

**Tests:** `tests/scenario.py: add_room` nimmt jetzt `trvs=[...]` statt `trv=...`.
