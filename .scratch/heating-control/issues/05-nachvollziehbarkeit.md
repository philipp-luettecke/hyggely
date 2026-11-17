# 05: Nachvollziehbarkeit: Grund, Logbuch, Diagnose

Spec: `.scratch/heating-control/spec.md`

**What to build:** Jeder Raum hat einen Grund-Sensor. Er erklärt in Klartext, warum gerade diese Solltemperatur gilt (z. B. „Komfort bis 22:00“). Als Attribut trägt er einen stabilen Grund-Code für Automationen. Jede Änderung des Sollwerts erscheint im Logbuch mit Grund. Der Admin kann einen Diagnose-Export herunterladen, der Konfiguration, aktuelle Raum-Schnappschüsse und die letzten Entscheidungen enthält. Spätere Tickets ergänzen ihre Gründe (Übersteuerung, Fenster, Abwesend, Urlaub) über denselben Mechanismus.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Pro Raum gibt es einen Grund-Sensor mit deutschem und englischem Klartext
- [ ] Der Grund-Code ist ein stabiler, dokumentierter Wert und als Attribut verfügbar
- [ ] Der Klartext nennt, wo sinnvoll, den nächsten Schaltpunkt (z. B. „Eco bis 06:30“)
- [ ] Jede Änderung des Sollwerts erzeugt genau einen Logbuch-Eintrag mit Grund
- [ ] Der Diagnose-Export enthält Konfiguration, Schnappschüsse und die letzten Entscheidungen ohne personenbezogene Daten über das Nötige hinaus
- [ ] Grund-Code und Parameter stammen aus dem Target Resolver. Der Sensor übersetzt sie nur
- [ ] Die Grund-Codes für spätere Eingaben (Übersteuerung, Aus, Fenster, Abwesend, Urlaub, Haus aus) sind schon definiert und übersetzt, sodass spätere Tickets den Sensor nicht umbauen müssen
- [ ] Szenario-Tests prüfen Grund-Code und Klartext für Komfort, Nacht und Eco sowie den Logbuch-Eintrag. Der Diagnose-Export hat einen eigenen Test
