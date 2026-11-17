# 05 – Nachvollziehbarkeit: Grund-Sensor, Logbuch, Diagnose

Status: ready-for-agent
Blocked by: 03
Spec: `.scratch/heating-control/spec.md`

## What to build

Jeder Raum bekommt einen **Grund**-Sensor. Er erklärt in Klartext (Deutsch und Englisch), warum der Raum gerade seinen Sollwert hat, etwa „Komfort bis 22:00“ oder „Eco bis 06:30“.

- Als Attribut trägt er einen stabilen Grund-Code mit Parametern, damit Automationen ihn auswerten können.
- Der Target Resolver liefert Grund-Code und Parameter. Der Sensor übersetzt sie nur.
- Grund-Codes für spätere Eingaben (Fenster, Übersteuerung, Abwesend, Urlaub, Aus) werden schon jetzt definiert und übersetzt. Sie greifen, sobald die jeweiligen Tickets fertig sind.

Jede Änderung des Sollwerts eines Raums erzeugt einen **Logbuch**-Eintrag am Raum-Thermostat mit dem Grund.

Die Integration bietet einen **Diagnose-Export** an. Er enthält:

- die Konfiguration (ohne personenbezogene Details)
- die aktuellen Raum-Schnappschüsse
- die letzten Entscheidungen pro Raum

## Acceptance criteria

- [ ] Grund-Sensor pro Raum zeigt Stufe und Ende der Stufe in Klartext; ändert sich mit dem Schaltpunkt
- [ ] Grund-Code und Parameter sind als Attribute verfügbar und dokumentiert
- [ ] Alle in der Spec genannten Gründe haben Übersetzungen (de/en)
- [ ] Logbuch-Eintrag bei jeder Sollwertänderung, mit Grund
- [ ] Diagnose-Export ist herunterladbar und enthält Konfiguration, Schnappschüsse, letzte Entscheidungen
- [ ] Szenario-Tests prüfen Grund-Sensor und Logbuch-Eintrag; Diagnose-Export hat einen Test

## Blocked by

- 03 – Ein Raum folgt dem Zeitplan
