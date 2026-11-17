# 11: Abwesend

Spec: `.scratch/heating-control/spec.md`

**What to build:** Sind alle im Haupteintrag konfigurierten Personen länger als die Abwesend-Verzögerung (Standard 30 min) nicht zu Hause, gilt Abwesend. Alle Räume im Modus Auto erhalten dann die Abwesend-Temperatur. Kommt jemand zurück, gilt sofort wieder die Zeitplan-Stufe. Eine unbekannte oder nicht erreichbare Anwesenheit gilt als „zu Hause“. Es gibt eine globale Entität „Abwesend“, und der Grund-Sensor zeigt „Abwesend“.

**Blocked by:** 03

**Status:** done

- [ ] Eine globale Entität zeigt, ob Abwesend gilt
- [ ] Abwesend gilt erst, wenn alle Personen länger als die Verzögerung weg sind
- [ ] Kehrt eine Person zurück, endet Abwesend sofort
- [ ] Eine Person mit unbekanntem oder nicht erreichbarem Zustand gilt als zu Hause
- [ ] Räume im Modus Auto erhalten bei Abwesend die globale Abwesend-Temperatur
- [ ] Der Grund-Sensor zeigt Abwesend
- [ ] Szenario-Tests decken Verzögerung, Rückkehr, unbekannte Anwesenheit und mehrere Personen ab

## Comments

**Modul `presence.py` (`Presence`):** Wird einmal pro Haupteintrag angelegt (`entry.runtime_data.presence`) und an jeden Room Controller übergeben. Jeder Raum abonniert die Änderungen und schreibt `away` in seinen `RoomSnapshot`. Im Target Resolver steht die Regel unter Raum `off` und Übersteuerung; Hausbetriebsart `off` und Urlaub (Ticket 12) kommen dazwischen, Fenster offen (Ticket 10) darüber. Neue Snapshot-Felder: `away` (Standard `False`) und `away_temperature` (Pflicht, aus den Optionen des Haupteintrags).

**Regeln:** Abwesend gilt, wenn alle konfigurierten Personen nicht `home` sind und das seit mindestens der Abwesend-Verzögerung. Jeder andere Zustand (`not_home`, eine Zone wie „Arbeit“) zählt als weg. Ein Wechsel zwischen solchen Zuständen startet die Verzögerung nicht neu. Kommt jemand kurz zurück, beginnt sie neu. `unknown`, `unavailable` und eine nicht vorhandene Personen-Entität zählen als zu Hause. Ohne konfigurierte Personen gilt nie Abwesend.

**Neustart/Neuladen:** Beim Start zählt die Verzögerung ab dem letzten `last_changed` der Personen. Eine Optionsänderung lässt ein abwesendes Haus also abwesend, statt 30 min hochzuheizen. Nach einem echten HA-Neustart setzt HA `last_changed` neu; dann läuft die Verzögerung erneut, im Zweifel also eher warm. `person` steht deshalb in `after_dependencies`.

**Entität:** `binary_sensor` „Abwesend“ (Zustände „Ja“/„Nein“, ohne Device-Class, weil `presence` „an = zu Hause“ bedeutet). Sie hängt an einem eigenen Gerät **„Haus“** (Kennung `(climate_control, <entry_id>)`, übersetzt über `translation_key="house"`), nicht an einem Raum. Ticket 12 kann Hausbetriebsart und Urlaubsende an dasselbe Gerät hängen (`DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})`). Unique ID `<entry_id>_away`. Icons in `icons.json`.

**Grund:** Der Target Resolver liefert `ReasonCode.AWAY = "away"` ohne Parameter. Den Grund-Sensor gab es beim Abschluss noch nicht (Ticket 05 läuft parallel), deshalb prüft noch kein Test den Text „Abwesend“. Wer 05 mit 11 zusammenführt, sollte in `tests/test_away.py` den Grund-Sensor im ersten Szenario mitprüfen.

**Tests:** `tests/test_away.py` mit echten `person`-Entitäten, die einem `device_tracker` pro Handy folgen (Fixture `persons`, `tests/scenario.py: Persons`). Neu in `scenario.py` sind außerdem `change_global_settings` (Optionsdialog des Haupteintrags) und `away_state`. In `pyproject.toml` ist für Tests zusätzlich `PLR0917` abgeschaltet (Fixtures als Positionsargumente), analog zu `PLR0913`.

**Abgeschlossen:** Merge-Commit `0d53a5a` auf `feat/heating-control`. Ergebnis: globales Abwesend mit Verzögerung und `binary_sensor` am Gerät „Haus“; Räume in Auto erhalten die Abwesend-Temperatur; 41 Tests grün.
