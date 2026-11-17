# 14: Benachrichtigungen mit Spam-Regeln

Spec: `.scratch/heating-control/spec.md`

**What to build:** Die im Haupteintrag gewählten Empfänger erhalten zwei Arten von Nachrichten: „Fenster seit 20 min offen“ und „TRV seit 30 min offline“. Dabei gelten folgende Regeln gegen Spam:
- Jedes Ereignis wird pro Raum nur einmal gemeldet. Neu gemeldet wird erst, wenn der Zustand sich auflöst und erneut eintritt.
- Gleichzeitige Ereignisse werden zu einer Nachricht gebündelt.
- Es gibt keine „wieder online“-Meldungen.
- In der Ruhezeit (Standard 22–7 Uhr) wird zurückgehalten. Danach wird gesammelt gemeldet, was noch zutrifft.

**Blocked by:** 10, 13

**Status:** ready-for-agent

- [ ] Nach 20 min offenem Fenster erhalten alle konfigurierten Empfänger genau eine Nachricht
- [ ] Nach 30 min nicht erreichbarem TRV erhalten alle konfigurierten Empfänger genau eine Nachricht
- [ ] Ein weiterhin bestehendes Ereignis erzeugt keine Wiederholung
- [ ] Löst sich ein Ereignis auf und tritt erneut ein, gibt es eine neue Nachricht
- [ ] Ereignisse mehrerer Räume, die innerhalb eines kurzen Bündelungsfensters eintreten, ergeben eine einzige Nachricht
- [ ] Es gibt keine Nachricht beim Auflösen eines Ereignisses
- [ ] In der Ruhezeit wird nichts gesendet. Am Ende der Ruhezeit kommt eine gesammelte Nachricht nur für noch bestehende Ereignisse
- [ ] Szenario-Tests decken einmaliges Melden, Bündelung, Ruhezeit und erneutes Eintreten ab

## Comments

**Umsetzung:** `notifier.py` (`Notifier`, einer pro Haupteintrag) hängt sich wie `repair_issues` an die Listener der Room Controller. „Fenster offen“ kommt aus dem neuen `RoomController.window_open_since` (aus `window.py`, also ab Öffnen des Kontakts, nicht ab Ablauf der Fenster-Verzögerung): fällig 20 min danach. „TRV offline“ ist `RoomController.offline_trvs` aus Ticket 13: fällig, sobald das TRV dort auftaucht. Versand über `notify.send_message` an die `notify_targets` des Haupteintrags mit Titel und Text; ohne Empfänger wird nichts gesendet. `notify` steht in `after_dependencies`.

**Entscheidung: Bündelungsfenster 1 min.** Wird das erste Ereignis fällig, wartet der Notifier 1 min und schickt dann **eine** Nachricht mit allem, was bis dahin fällig und noch nicht gemeldet ist. Folge: Die Fenster-Nachricht kommt nach 21 min, die TRV-Nachricht nach 31 min. Ein Bridge-Ausfall trifft alle TRVs zur selben Minutenabfrage und landet damit sicher in einer Nachricht. Fenster, die mehr als 1 min auseinander fällig werden, ergeben getrennte Nachrichten. Löst sich ein Ereignis innerhalb des Bündelungsfensters auf, wird es nicht gemeldet.

**Entscheidung: ein Ereignis pro TRV.** „TRV offline“ wird pro TRV gemeldet (mit Name und Raum), „Fenster offen“ pro Raum. Bei mehreren TRVs pro Raum (Ticket 09) wird ein später ausfallendes zweites TRV also eigens gemeldet. Wiederholt wird erst, wenn das Ereignis sich aufgelöst hat (Fenster zu, TRV zurück) und erneut fällig wird.

**Ruhezeit:** Fällige Ereignisse werden in der Ruhezeit (Haupteintrag, Standard 22–7 Uhr, darf über Mitternacht gehen; Beginn = Ende heißt keine Ruhezeit) zurückgehalten. Genau zum Ende kommt eine gesammelte Nachricht mit dem, was dann noch zutrifft. Ein Bündelungsfenster, das in die Ruhezeit hineinläuft, wird ebenfalls bis zum Ende zurückgehalten.

**Texte:** Deutsch und Englisch nach der Sprache von Home Assistant zum Sendezeitpunkt, in den Übersetzungen unter `common` (die einzige freie Kategorie, die hassfest zulässt). Titel „Heizung“; eine Zeile pro Art, Räume bzw. TRVs alphabetisch, z. B.
„Fenster seit über 20 min offen: Bad, Wohnzimmer“
„Heizkörperthermostat seit über 30 min nicht erreichbar: Thermostat Bad (Bad)“

**Neuladen und Neustart:** Gemeldete Ereignisse überstehen ein Neuladen des Eintrags (Optionsdialog, Raum ändern) über `hass.data`, damit es keine Wiederholung gibt. Nach einem Neustart von Home Assistant wird ein noch bestehendes Ereignis erneut gemeldet, sobald es wieder fällig ist: Fenster- und Offline-Dauer zählen ab dem Neustart (Ticket 10 und 13), also frühestens 20 bzw. 30 min danach. Das schien vertretbar und spart einen eigenen Speicher; sonst nachrüstbar.

**Tests:** `tests/test_notifications.py` (Fenster nach 20 min an alle Empfänger, keine Wiederholung, TRV offline, Bridge-Ausfall, keine Meldung beim Auflösen, erneutes Eintreten von Fenster und TRV, Auflösen im Bündelungsfenster, Bündelung über mehrere Räume, getrennte Nachrichten, Ruhezeit mit Sammelnachricht um 7 Uhr, in der Nacht aufgelöstes Ereignis, Ruhezeit aus den Einstellungen, Englisch, Neuladen, geänderte Empfänger). Neue Test-Hilfe `tests/simulated_phone.py` (Fixture `phones`): Handys als echte `notify`-Entitäten mit Titel, wie die Companion App.
