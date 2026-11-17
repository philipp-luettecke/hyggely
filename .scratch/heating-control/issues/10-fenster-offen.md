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
