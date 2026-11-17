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
