# 12: Hausbetriebsart und Urlaub mit Enddatum

Spec: `.scratch/heating-control/spec.md`

**What to build:** Eine globale Auswahl-Entität „Hausbetriebsart“ bietet Automatik, Urlaub und Aus. Zusätzlich gibt es eine Datum-Uhrzeit-Entität „Urlaubsende“. Bei Urlaub erhalten alle Räume die Urlaubstemperatur. Ist das Urlaubsende erreicht, wechselt die Hausbetriebsart automatisch auf Automatik. Bei Aus erhalten alle Räume Frostschutz. Eine Übersteuerung schlägt Urlaub, Aus und Abwesend. Das Fenster schlägt alles. Beide Entitäten überstehen einen Neustart und lassen sich per Siri oder Automation steuern. Damit ist die vollständige Rangfolge aus der Spec umgesetzt.

**Blocked by:** 06

**Status:** done

- [ ] Die Hausbetriebsart ist als Auswahl-Entität mit Automatik, Urlaub und Aus verfügbar
- [ ] Das Urlaubsende ist als Datum-Uhrzeit-Entität verfügbar. Bei Erreichen wechselt die Hausbetriebsart auf Automatik
- [ ] Bei Urlaub gilt die Urlaubstemperatur in allen Räumen ohne Übersteuerung
- [ ] Bei Aus gilt Frostschutz in allen Räumen ohne Übersteuerung
- [ ] Eine Übersteuerung wirkt auch bei Urlaub, Aus und Abwesend
- [ ] Hausbetriebsart und Urlaubsende überstehen einen Neustart
- [ ] Der Grund-Sensor zeigt Urlaub (mit Ende) bzw. „Haus aus“
- [ ] Szenario-Tests decken die vollständige Rangfolge Fenster > Aus > Übersteuerung > Haus aus > Urlaub > Abwesend > Zeitplan ab

## Comments

**Module:** `house_mode.py` (`HouseModeController`, einer pro Haupteintrag, `entry.runtime_data.house_mode`) hält Hausbetriebsart und Urlaubsende. Er ist die einzige Stelle, die beides ändert: `async_set_house_mode(HouseMode)` und `async_set_vacation_end(datetime)`. Die Entitäten `select.py` („Hausbetriebsart“, Optionen `auto`/`vacation`/`off`, übersetzt Automatik/Urlaub/Aus) und `datetime.py` („Urlaubsende“) reichen nur durch. **Für Ticket 20:** Die Panel API ruft dieselben zwei Methoden auf; die Fehlermeldung bei Urlaub ohne Ende kommt als `ServiceValidationError` (`translation_key="vacation_end_not_ahead"`). Beide Entitäten hängen am Gerät „Haus“ aus Ticket 11 (`house_mode.house_device_info`, jetzt auch vom Abwesend-Sensor genutzt). Unique IDs `<entry_id>_house_mode` und `<entry_id>_vacation_end`.

**Rangfolge im Target Resolver:** Neue Snapshot-Felder `house_mode`, `vacation_end`, `vacation_temperature`; neue Stufe `Level.VACATION`. Haus aus → Frostschutz mit TRV `off` (wie Raum aus und Fenster), Grund `house_off`; Urlaub → Urlaubstemperatur mit `heat`, Grund `vacation` mit `until` = Urlaubsende („Urlaub bis 20.11. 18:00“). Das Raum-Thermostat bleibt dabei auf Auto. „Haus aus > Urlaub“ ist automatisch erfüllt, weil die Hausbetriebsart nur einen Wert hat.

**Entscheidung: Urlaub ohne Urlaubsende in der Zukunft.** Urlaub läuft nie unbefristet. Ist kein Urlaubsende gesetzt oder liegt es nicht in der Zukunft, wird die Auswahl „Urlaub“ abgelehnt (Fehlermeldung „Urlaub braucht ein Urlaubsende in der Zukunft. Setze zuerst das Urlaubsende.“), die Hausbetriebsart bleibt unverändert. Per Siri/Automation also zuerst das Urlaubsende setzen, dann Urlaub wählen. Wird das Urlaubsende während des Urlaubs auf jetzt oder die Vergangenheit gesetzt, endet der Urlaub sofort (Auto); ein späteres Ende verlängert ihn. Nach Ablauf bleibt das Urlaubsende als Wert stehen.

**Entscheidung: Heizen ohne Temperatur bei Haus aus.** Wie in 07 für Raum aus entschieden (dort noch `needs-info`), übersteuert „Heizen“ bei Haus aus nicht mit dem Frostschutz, sondern mit dem Sollwert, den Auto ohne „Haus aus“ hätte (Zeitplan-Stufe bzw. Abwesend), siehe `target_resolver.heat_temperature`. Bei Urlaub gilt der Spec-Wortlaut: Heizen übersteuert mit der Urlaubstemperatur. Wird die Frage aus 07 anders entschieden, gilt das für Haus aus mit.

**Speicherung:** Eigener `Store` `.storage/climate_control.<entry_id>.house_mode`, jede Änderung wird sofort geschrieben (wie 06). Beim Start ist ein inzwischen abgelaufener Urlaub sofort Auto. Beim Entfernen der Integration wird die Datei gelöscht.

**Nebenbei behoben (Room Controller):** An einem Schaltpunkt fordern der Neubewertungs-Timer und der Zeitplan-Helfer gleichzeitig eine Bewertung an. Welche zuerst lief, hing von der Reihenfolge der Timer in der Event-Loop ab; mit einem gerade verlorenen Befehl (Bridge-Ausfall) ging er dann doppelt raus. Die zusätzlichen Plattformen haben diese Reihenfolge verschoben, sodass `test_command_lost_before_the_outage_was_noticed_is_sent_again` (13) fehlschlug. Gleichzeitige Anforderungen werden jetzt zu einer Bewertung zusammengefasst.

**Tests:** `tests/test_house_mode.py` (Urlaub in allen Räumen bis zum Ende, Grund-Text, Ablehnung ohne künftiges Ende, Ende verschieben/vorziehen, Haus aus, Übersteuerung > Urlaub, Übersteuerung > Haus aus, Raum aus > Haus aus, Urlaub > Abwesend, Haus aus > Abwesend, Fenster > Urlaub/Haus aus/Abwesend, Heizen bei Haus aus und Urlaub, Neustart mit Urlaub, Urlaub während des Neustarts abgelaufen, Neustart mit Haus aus, geänderte Urlaubstemperatur). Fenster > Raum aus deckt `test_window_open.py` ab, Übersteuerung > Abwesend und Abwesend > Zeitplan `test_away.py`. Hilfe `House` in `tests/scenario.py`; Übersetzungstest in `tests/test_translations.py`.

**Abgeschlossen:** Merge-Commits `6b18908` und `fd421ff` (Rangfolge als geordnete Regelliste) auf `feat/heating-control`. Ergebnis: Hausbetriebsart und Urlaubsende am Gerät „Haus“, vollständige Rangfolge per Szenario getestet; 142 Tests grün. Heizen ohne Temperatur bei „Haus aus“ folgt der offenen Frage aus Ticket 07.
