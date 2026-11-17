# 04: Stufe Nacht, Vorlaufzeit und nächster Schaltpunkt

Spec: `.scratch/heating-control/spec.md`

**What to build:** Blöcke im Zeitplan tragen in ihren Zusatzdaten eine Stufe (`level`: `comfort` oder `night`). Ein Block ohne Angabe gilt als Komfort, außerhalb von Blöcken gilt Eco. Der Raum bekommt zusätzlich eine Temperatur für Nacht und eine Vorlaufzeit. Beginnt ein Block innerhalb der Vorlaufzeit, gilt bereits seine Stufe. Das Bad ist so morgens zum Blockbeginn warm. Das Raum-Thermostat kennt außerdem den nächsten Schaltpunkt als Attribut. Ihn brauchen spätere Tickets für den Rückfall.

**Blocked by:** 03

**Status:** needs-info

- [ ] Ein Block mit `level: night` setzt die Nacht-Temperatur, ein Block ohne Angabe die Komfort-Temperatur
- [ ] Bei aneinandergrenzenden Blöcken mit unterschiedlicher Stufe wechselt die Solltemperatur genau an der Grenze
- [ ] Mit einer Vorlaufzeit von z. B. 30 min wird die Stufe eines Blocks 30 min vor seinem Beginn angewendet
- [ ] Die Vorlaufzeit wirkt nur auf den Beginn eines Blocks. Beim Blockende wird nicht vorzeitig abgesenkt
- [ ] Der Blockbeginn um Mitternacht, Blöcke über den Tageswechsel und der Wochenwechsel von Sonntag auf Montag verhalten sich korrekt
- [ ] Der nächste Schaltpunkt ist als Attribut verfügbar, berücksichtigt die Vorlaufzeit und wird bei einer Änderung am Zeitplan neu berechnet
- [ ] Das Raum-Thermostat zeigt die aktive Stufe als Attribut
- [ ] Nacht-Temperatur und Vorlaufzeit sind im Optionsdialog des Raums änderbar
- [ ] Szenario-Tests decken Stufen, Vorlaufzeit und Grenzfälle am Tageswechsel ab

## Comments

**Frage (needs-info): Vorlaufzeit bei aneinandergrenzenden Blöcken, wenn der zweite Block kälter ist.** Beispiel: Komfort 17:00–22:00, direkt danach Nacht 22:00–24:00, Vorlaufzeit 30 min. Nach der umgesetzten Regel gilt Nacht schon ab 21:30. Das passt wörtlich zu „Beginnt ein Block innerhalb der Vorlaufzeit, gilt bereits seine Stufe“. Es widerspricht aber „Beim Blockende wird nicht vorzeitig abgesenkt“ und „wechselt genau an der Grenze“. Optionen:
- **A (umgesetzt):** Die Vorlaufzeit gilt für jeden Blockbeginn. Abends wird dann ggf. um die Vorlaufzeit früher auf Nacht abgesenkt.
- **B:** Die Vorlaufzeit gilt nur, wenn die Stufe des neuen Blocks im Raum wärmer ist als die bisherige. Vorgeheizt wird also, früher abgesenkt nie. Das erfüllt beide No-Gos. Der Schedule Reader bräuchte dafür die Stufentemperaturen des Raums.
- **C:** Die Vorlaufzeit gilt nur nach Eco, nicht nach einem angrenzenden Block. Dann wäre das Bad nach einem Nacht-Block morgens nicht vorgeheizt („morgens kalt“).

Empfehlung: B. Die Änderung bleibt auf `schedule_reader.py` begrenzt, kein Test legt den strittigen Fall bisher fest. Alle übrigen Kriterien sind umgesetzt und getestet.

**Schedule Reader:** Er liest die Blöcke über `schedule.get_schedule`, beim Start und bei jeder Meldung des Helfers neu. Abonniert sind `state_changed` und `state_reported`, denn eine Änderung an einem künftigen Block lässt Zustand und Attribute des Helfers oft unverändert (per Test abgesichert). Stufe aus `data.level`: `night` ergibt Nacht, alles andere oder keine Angabe Komfort, außerhalb der Blöcke gilt Eco. `next_event` und der Zustand des Helfers bestimmen die Stufe nicht mehr; der Zustand zeigt nur noch an, ob der Helfer verfügbar ist. Gerechnet wird in UTC, weil die Vorlaufzeit eine Dauer ist. Ein Block bis `24:00` geht nahtlos in einen Block ab `00:00` am Folgetag über.

**Vorlaufzeit-Regel:** Beginnt der nächste Block innerhalb der Vorlaufzeit, gilt seine Stufe, auch wenn gerade ein anderer Block läuft. Das Ende eines Blocks (Übergang zu Eco) wird nie vorgezogen. Beispiel Bad: Nacht 00:00–06:30, Komfort ab 06:30, Vorlaufzeit 30 min, also Komfort ab 06:00. Vorlaufzeiten über einen Tag werden nicht unterstützt.

**Nächster Schaltpunkt:** Das ist der nächste Zeitpunkt, an dem sich die wirksame Stufe ändert (Glossar), die Vorlaufzeit eingerechnet. Ändert sich die Stufe nie (z. B. leerer Zeitplan), ist er `None`. Für 06/07: `ScheduleReader.read()` hat seine Signatur behalten. Rückfall und Aus enden damit am vorgezogenen Schaltpunkt, z. B. 06:30 statt 07:00.

**Attribute des Raum-Thermostats:** `level` ist die aktive Stufe: `comfort`/`night`/`eco` aus dem Zeitplan, `away` bei Abwesend (11), `frost` bei Aus, `None` bei Übersteuerung. `next_block_boundary` ist ein `datetime`. `Level` kennt jetzt auch `away` und `frost`. `Decision.level` ist ein neues Pflichtfeld; neue Regeln (Fenster, Hausbetriebsart, Urlaub) müssen es setzen.

**Raum-Daten:** Neu sind `night_temperature` (Standard 17 °C) und `lead_time` (Dauer wie `away_delay`, Standard 0 min). Räume ohne diese Felder bekommen die Standardwerte. Bitte die Standardwerte bei Bedarf anpassen.

**Tests:** `tests/test_levels_and_lead_time.py`. `scenario.block()` nimmt optional eine Stufe, `living_room()` beliebige Blöcke pro Wochentag und `lead_minutes`, `scenario.local()` liefert Zeitpunkte in Ortszeit.
