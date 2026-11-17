# 13: Ausfälle

Spec: `.scratch/heating-control/spec.md`

**What to build:** Die Integration bleibt robust, wenn TRVs oder Home Assistant ausfallen.

Grundlage ist das Messprotokoll in Ticket 01. Fällt die Bridge aus, wird die `climate`-Entität des TRV **nicht** `unavailable`, sondern friert mit alten Werten ein. Nur der Temperatursensor desselben Geräts wird nach ca. 1,5 min `unavailable`. Nach dem Wiedereinstecken dauert es über 3 min, bis wieder frische Werte kommen. Dazwischen kann die Bridge kurz einen ungültigen Modus (`None`) melden.

Verhalten:
- **Nicht erreichbar:** Ein TRV gilt als nicht erreichbar, wenn seine `climate`-Entität **oder** der Temperatursensor desselben Geräts `unavailable` ist. Der Sensor wird beim Einrichten des Raums automatisch über das Gerät gefunden.
- **Wieder erreichbar:** Wird ein TRV wieder erreichbar, erhält es seinen Sollzustand erneut, sobald die `climate`-Entität einen gültigen Modus meldet.
- **Ungültige Meldungen:** Ein ungültiger Modus und eingefrorene Werte während eines Ausfalls lösen weder Befehle noch Übersteuerungen aus.
- **Neustart von Home Assistant:** Die TRVs werden gestaffelt angesteuert, nicht alle gleichzeitig.
- **Reparaturhinweis:** Ein TRV, das länger als 30 min nicht erreichbar ist, erscheint unter Reparaturen. Der Hinweis verschwindet von selbst, wenn das TRV zurück ist.

**Blocked by:** 01, 03

**Status:** ready-for-agent

- [ ] Ein TRV gilt als nicht erreichbar, wenn die `climate`-Entität oder der Temperatursensor des Geräts `unavailable` ist
- [ ] Der Temperatursensor wird ohne Zutun des Admins über das Gerät des TRV gefunden. Fehlt er, zählt nur die `climate`-Entität
- [ ] Während der Nichterreichbarkeit gehen keine Befehle an das TRV, und eingefrorene Werte erzeugen keine Übersteuerung
- [ ] Ein wieder erreichbares TRV erhält den aktuellen Sollzustand, sobald es einen gültigen Modus meldet
- [ ] Ein ungültiger Modus (`None`) wird ignoriert
- [ ] Nach einem Neustart werden die Befehle an mehrere TRVs gestaffelt gesendet
- [ ] Nach 30 min Nichterreichbarkeit gibt es genau einen Reparaturhinweis pro TRV, der bei Rückkehr verschwindet
- [ ] Die simulierten TRVs bilden das gemessene Ausfallverhalten nach (Einfrieren, Sensor `unavailable`, verzögerte Rückkehr, kurzzeitig `None`)
- [ ] Szenario-Tests decken Ausfall, Rückkehr, ungültigen Modus, gestaffelten Start und Reparaturhinweis ab

## Comments

**Module:**
- `trv_reachability.py` (`TrvReachability`, einer pro Raum): findet beim Start des Raums den Temperatursensor über das Gerät des TRV (Entity-Registry, Domäne `sensor`, Geräteklasse `temperature`). Ohne Sensor zählt nur die `climate`-Entität. Ein TRV „nimmt Befehle an“, wenn es erreichbar ist und `heat` oder `off` meldet. Konnte es das zwischendurch nicht (nicht erreichbar, ungültiger Modus, fehlender Zustand), meldet das Modul es zurück, sobald es wieder Befehle annimmt.
- `command_pacer.py` (`CommandPacer`, einer pro Haupteintrag): führt Nachhol-Befehle aller Räume mit **2 s Abstand** aus, der erste sofort. Nachhol-Befehle sind (a) die ersten Befehle beim Start, solange Home Assistant noch nicht `running` ist, und (b) das erneute Senden an zurückgekehrte TRVs. Bei 20 TRVs ist das letzte nach ca. 40 s versorgt. Reaktionen auf Entscheidungen (Schaltpunkt, Bedienung) gehen weiter sofort raus. Beim Neuladen des Eintrags im laufenden Betrieb wird nicht gestaffelt, damit Optionsänderungen sofort wirken.
- `repair_issues.py`: hält pro Offline-TRV einen Reparaturhinweis (`trv_offline_<entity_id>`, Warnung, nicht reparierbar, nicht persistent) und löscht ihn bei Rückkehr oder beim Entladen des Raums.
- `RoomController`: sendet nur an TRVs, die Befehle annehmen. Ein zurückgekehrtes TRV erhält den aktuellen Sollzustand **unbedingt erneut**, auch wenn sein eingefrorener Zustand passt, weil Befehle aus der unbemerkten ersten Minute des Ausfalls verloren gehen (Szenario-Test).

**Für Ticket 14:** Die 30-min-Bedingung ist von außen beobachtbar: `RoomController.offline_trvs` (Menge der Entity-IDs) plus `async_add_listener`, der bei jeder Änderung aufgerufen wird. Der Notifier kann sich genauso anhängen wie `repair_issues.async_track_offline_trvs`. Seit wann ein TRV nicht erreichbar ist, kommt aus `last_changed` der `unavailable`-Zustände. Deshalb übersteht die Bedingung ein Neuladen des Eintrags, und nach einem Neustart zählt die Zeit ab dem Neustart.

**Für Ticket 08/09:** Eingefrorene Werte und der Modus `None` erzeugen keine Befehle. Eine Übersteuerungserkennung muss Zustandsänderungen von TRVs ignorieren, die gerade keine Befehle annehmen (`TrvReachability.takes_commands`). Die Ist-Temperatur des Raums zählt eingefrorene Werte noch mit. Das Ausschließen nicht erreichbarer TRVs vom Mittelwert gehört zu Ticket 09.

**Simulierte TRVs:** Jedes TRV hat jetzt `sensor.<id>_current_temperature` am selben Gerät (abschaltbar mit `temperature_sensor=False`). Home Assistant fragt jede volle Minute ab (`SimulatedTrv._poll`). Ticket 08 kann dort die Drehungen am Knopf zustellen. `unplug_bridge()` friert ein, Befehle gehen verloren, und der Sensor ist ab der zweiten Abfrage `unavailable`. `plug_in_bridge()` bringt den Sensor zur zweiten Abfrage zurück, zusammen mit dem Modus `None` (Zustand `unknown`). Frische Werte kommen zur vierten Abfrage, wie in Ticket 01 gemessen. Außerdem gibt es `report_invalid_mode()` und `set_available()`.

**Annahme:** Ein ungültiger Modus ohne Ausfall wird genauso behandelt wie eine Rückkehr: keine Befehle während `unknown`, danach einmal der aktuelle Sollzustand.
