# 15: Klickbarer Panel-Prototyp

Spec: `.scratch/heating-control/spec.md`

**What to build:** Ein Wegwerf-Prototyp des Heating Panel als einzelne HTML-Datei mit Beispieldaten (5 Räume, ein geteilter Zeitplan, eine laufende Übersteuerung, ein offenes Fenster). Er läuft auf dem Handy im Browser und zeigt alle Inhalte aus der Spec:
- Raumübersicht mit Ist, Soll, Modus und Grund; Antippen beendet die Übersteuerung
- Wochenraster pro Zeitplan mit Blöcken und Stufen sowie „gilt für“-Anzeige
- Stufentemperaturen und Vorlaufzeit pro Raum
- Hausbetriebsart und Urlaub mit Enddatum
- Zeitplan für einen Raum anlegen

Es gibt keine Verbindung zu Home Assistant. Wenn es Gestaltungsfragen gibt, z. B. wie Blöcke auf dem Handy am bequemsten verschoben werden, zeigt der Prototyp zwei oder drei Varianten, zwischen denen sich umschalten lässt. Umgesetzt wird mit dem Skill `prototype`.

**Blocked by:** None (can start immediately)

**Status:** done

- [ ] Eine einzelne HTML-Datei, ohne Build-Schritt auf dem Handy öffnenbar
- [ ] Alle fünf Inhalte aus der Spec sind mit Beispieldaten bedienbar
- [ ] Für das Bearbeiten von Blöcken im Wochenraster gibt es mindestens zwei umschaltbare Varianten
- [ ] Die Texte sind auf Deutsch und verwenden die Begriffe aus dem Glossar
- [ ] Eine kurze Liste offener Gestaltungsfragen für die Abnahme in Ticket 16 liegt bei

## Comments

- Kein Merge (Wegwerf-Prototyp, wird nicht in die Integration übernommen): liegt auf Branch `prototype/15-panel`, Commit `636ce5c`. Datei `prototypes/heating-panel/heating-panel-prototype.html`, offene Fragen für Ticket 16 in `prototypes/heating-panel/OPEN-QUESTIONS.md` (12 Fragen, u. a. Wahl der Variante A/B/C fürs Wochenraster). Ergebnis: Eine Offline-HTML-Datei mit allen fünf Panel-Inhalten, drei Varianten über `?variant=`, Selbsttest über `?selftest=1` ohne JS-Fehler.
