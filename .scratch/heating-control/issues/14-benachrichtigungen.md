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
