# 10: Fenster offen

Spec: `.scratch/heating-control/spec.md`

**What to build:** Der Admin ordnet einem Raum Fensterkontakte zu. Ist irgendeiner davon länger als die Fenster-Verzögerung (Standard 60 s) offen, geht der Raum auf Frostschutz. Das hat Vorrang vor allem anderen, auch vor einer Übersteuerung und vor Aus. Beim Schließen des letzten offenen Kontakts kehrt sofort der vorherige Zustand zurück, eine laufende Übersteuerung samt Rückfallzeitpunkt eingeschlossen. Läuft der Rückfall während des offenen Fensters ab, gilt nach dem Schließen die Zeitplan-Stufe. Ein nicht erreichbarer Kontakt gilt als geschlossen. Der Grund-Sensor zeigt „Fenster offen seit N min“.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Im Einrichtungs- und Optionsdialog eines Raums lassen sich null oder mehr Fensterkontakte wählen
- [ ] Ein Kontakt, der kürzer als die Verzögerung offen ist, ändert nichts
- [ ] Nach Ablauf der Verzögerung erhält das TRV Frostschutz
- [ ] Beim Schließen wird sofort der vorherige Zustand wiederhergestellt, inklusive Übersteuerung
- [ ] Ein während des offenen Fensters abgelaufener Rückfall führt nach dem Schließen zur Zeitplan-Stufe
- [ ] Ein nicht erreichbarer oder unbekannter Kontakt gilt als geschlossen
- [ ] Eine Drehung am TRV bei offenem Fenster ändert die gemerkte Übersteuerung, das TRV bleibt aber auf Frostschutz
- [ ] Der Grund-Sensor zeigt das offene Fenster mit Dauer
- [ ] Szenario-Tests decken Verzögerung, mehrere Kontakte, Wiederherstellung und nicht erreichbare Kontakte ab

## Comments

**Umsetzung:** Raum-Einstellung `window_contacts` (Liste von `binary_sensor`-Entitäten, optional, Standard leer) im Einrichtungs- und Optionsdialog des Raums. `window.py` (`WindowContacts`, eine Instanz pro Raum im Room Controller) liefert `open_since`: Ein Kontakt ist offen bei Zustand `on`; `off`, `unknown`, `unavailable` oder fehlend gilt als geschlossen. Offen ist das Fenster, sobald der am frühesten geöffnete, noch offene Kontakt die Fenster-Verzögerung (globale Einstellung aus 02) überschritten hat; `since` ist dessen Öffnungszeitpunkt (`last_changed`). Der Target Resolver hat das neue Feld `RoomSnapshot.window_open_since` und prüft es als erste Regel: Frostschutz, TRV `off` (wie bei Aus), Grund `window_open` mit `since`.

**Entscheidung: Raum-Modus bei offenem Fenster.** Das Raum-Thermostat zeigt weiter den gewählten Modus (Auto, Heizen oder Aus) samt Rückfallzeitpunkt, als Solltemperatur aber den Frostschutz. Grund: Würde es „Aus“ zeigen, tippt man in Apple Home naheliegend auf „Auto“ und beendet damit die gemerkte Übersteuerung. Der Rückfall läuft weiter: Endet die Übersteuerung bei offenem Fenster, steht der Raum sofort auf Auto, und nach dem Schließen gilt die Zeitplan-Stufe.

**Entscheidung: Bedienung bei offenem Fenster.** Eine neue Temperatur am Raum-Thermostat wird als Übersteuerung gemerkt (mit Rückfallzeitpunkt ab jetzt); das TRV bleibt aus, nach dem Schließen gilt sie. „Heizen“ ohne Temperatur übersteuert, wie in 07 für Aus entschieden, nicht mit dem Frostschutz, sondern mit dem Sollwert, den der Raum nach dem Schließen hätte (`target_resolver.heat_temperature` lässt das Fenster weg). „Aus“ und „Auto“ wirken auf den gemerkten Modus.

**Drehknopf bei offenem Fenster (Kriterium 7):** Über das Raum-Thermostat umgesetzt und getestet. Der Fall „Drehung am TRV“ hängt an Ticket 08, das beim Abschluss dieses Tickets noch nicht in `feat/heating-control` war. Erwartung: Läuft die erkannte externe Änderung über `RoomController.async_set_override`, merkt der Raum die Übersteuerung und schickt das TRV sofort wieder auf `off`, weil es vom Frostschutz abweicht. Wer als Zweiter merged, ergänzt dazu einen Szenario-Test (Fenster offen, `trv.report(target_temperature=…)` beim Abfragetakt → TRV wieder `off`, nach dem Schließen die gedrehte Temperatur).

**Hausbetriebsart (Ticket 12):** Fenster offen steht über allem, also auch über „Haus aus“ und Urlaub. Ticket 12 lief parallel; Tests für Fenster > Haus aus/Urlaub ergänzt, wer als Zweiter merged.

**Randfälle:** Wird ein Kontakt nicht erreichbar und danach wieder `on`, beginnt die Verzögerung neu (neues `last_changed`). Beim Neuladen des Eintrags (Optionsänderung) bleibt ein offenes Fenster sofort offen. Nach einem Neustart von Home Assistant zählt die Verzögerung ab dem Zeitpunkt, zu dem der Kontakt seinen Zustand nach dem Start meldet; ein offenes Fenster heizt dann höchstens eine Verzögerung lang weiter. Die Auswahl der Kontakte ist nicht auf Geräteklassen (`window`, `door`, `opening`) eingeschränkt, damit auch Kontakte ohne Geräteklasse wählbar sind.

**Zur Entscheidung (Logbuch-Rauschen, aus 05):** Geprüft mit echtem Logbuch (In-Memory-Recorder): Ja, bei offenem Fenster schreibt Home Assistant **jede Minute** einen Logbuch-Eintrag für den Grund-Sensor („Wohnzimmer Grund wechselte zu Fenster offen seit 1 min“, „… 2 min“, …), dazu einmal den Sollwert-Eintrag „7 °C (Fenster offen seit 1 min)“. Ein Text-Sensor ohne Einheit gilt im Logbuch nicht als kontinuierlich und wird nicht ausgefiltert; die Integration kann einzelne Entitäten nicht selbst vom Logbuch ausnehmen. Jede Minute entsteht außerdem eine Zeile in der Recorder-Historie. Umgesetzt ist weiter der Spec-Wortlaut „Fenster offen seit N min“. Optionen:
1. So lassen (Spec-Wortlaut). Rauschen nur, solange gelüftet wird; wen es stört, schließt den Grund-Sensor in der Logbuch-/Recorder-Konfiguration aus (dann fehlen dort aber auch die übrigen Grund-Wechsel).
2. Fester Text mit Uhrzeit, z. B. „Fenster offen seit 14:03“. Kein Rauschen; Änderung nur in den Übersetzungen (`window_open_since` mit `{since}`) und in `reason_text.py`. Die minütliche Aktualisierung entfällt.
3. Sensor-Zustand nur „Fenster offen“, die Dauer zeigt das Panel (Ticket 17) aus dem Attribut `since`. Kein Rauschen, aber der Sensor selbst nennt keine Dauer mehr.
4. Gröbere Stufen (z. B. 1, 5, 10, 20, 30 min, dann stündlich). Weniger Rauschen, der Text bleibt eine Dauer, ist aber ungenauer.

Empfehlung: Option 2, weil sie Klartext und ruhiges Logbuch verbindet. Bitte entscheiden; ohne Rückmeldung bleibt Option 1.

**Tests:** `tests/test_window_open.py` (Verzögerung, eigene Fenster-Verzögerung, kurzes Lüften, Wiederherstellung von Zeitplan-Stufe und Übersteuerung samt Rückfallzeitpunkt, Rückfall während offenem Fenster, Fenster über Aus, mehrere Kontakte, nicht erreichbare und unbekannte Kontakte, Grund mit minütlich steigender Dauer, Temperatur und Heizen bei offenem Fenster, Neuladen, Kontakte im Optionsdialog). Hilfe `WindowContact` in `tests/scenario.py`.
