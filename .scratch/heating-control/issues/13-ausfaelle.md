# 13: Ausfälle

Spec: `.scratch/heating-control/spec.md`

**What to build:** Die Integration bleibt robust, wenn TRVs oder Home Assistant ausfallen.
- Wird ein TRV wieder erreichbar, erhält es sofort seinen Sollzustand.
- Springt ein TRV nach einem Befehl von selbst auf `off` zurück (laut Ticket 01), wird das erkannt und begrenzt oft korrigiert.
- Nach einem Neustart von Home Assistant werden die TRVs gestaffelt und nicht alle gleichzeitig angesteuert.
- Ein TRV, das länger als 30 min nicht erreichbar ist, erscheint als Hinweis unter Reparaturen. Der Hinweis verschwindet von selbst, wenn das TRV zurück ist.

Das Verhalten der Bridge bei einem Stromausfall aus Ticket 01 ist in den simulierten TRVs nachgebildet.

**Blocked by:** 01, 03

**Status:** ready-for-agent

- [ ] Ein wieder erreichbares TRV erhält ohne weiteres Zutun den aktuellen Sollzustand
- [ ] Ein Zurückspringen auf `off` nach einem eigenen Befehl wird korrigiert, mit einer festen Obergrenze an Versuchen
- [ ] Nach Erreichen der Obergrenze erscheint ein Logbuch-Eintrag statt weiterer Versuche
- [ ] Nach einem Neustart werden die Befehle an mehrere TRVs gestaffelt gesendet
- [ ] Nach 30 min Nichterreichbarkeit gibt es genau einen Reparaturhinweis pro TRV, der bei Rückkehr verschwindet
- [ ] Szenario-Tests decken Wiederverfügbarkeit, Zurückspringen, gestaffelten Start und Reparaturhinweis ab
