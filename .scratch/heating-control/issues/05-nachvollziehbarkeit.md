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

## Comments

**Grund-Codes (stabil, Attribut `reason_code` des Grund-Sensors):** Der Target Resolver liefert `Reason(code=ReasonCode.…, params={…})`. Spätere Tickets setzen nur Code und Parameter, Sensor und Logbuch übersetzen.

| Code | Parameter | Klartext (de) |
|---|---|---|
| `comfort`, `night`, `eco` | `until`: nächster Schaltpunkt | „Komfort bis 09:00“, „Nacht bis …“, „Eco bis …“ |
| `override` | `until`: Rückfallzeitpunkt | „Heizen bis 14:00 (manuell)“ |
| `room_off` | `until`: nächster Schaltpunkt | „Aus bis 17:00“ |
| `window_open` | `since`: Zeitpunkt, seit dem das Fenster offen ist | „Fenster offen seit 4 min“ |
| `away` | keine | „Abwesend“ |
| `vacation` | `until`: Urlaubsende | „Urlaub bis 24.12. 18:00“ |
| `house_off` | keine | „Haus aus“ |

- Parameter sind `datetime` (aware) oder `None`. Ist `until` `None`, erscheint der Text ohne Zeit („Komfort“, „Heizen (manuell)“). Die Zeitplan-Stufen haben denselben Wert wie ihr Code (`ReasonCode(level.value)`).
- Texte stehen in den Übersetzungen unter `entity.sensor.reason.state`: `<code>`, `<code>_until` (Platzhalter `{until}`) und `window_open_since` (Platzhalter `{minutes}`). Zeit innerhalb der nächsten 24 h als „HH:MM“, sonst mit Datum („23.11. 07:00“, englisch „2026-11-23 07:00“). Sprache ist die von Home Assistant; ein Sprachwechsel übersetzt sofort neu.
- Attribute des Grund-Sensors: `reason_code` plus die Parameter (`until`/`since`).
- **Für Ticket 10:** Mit `since` aktualisiert sich der Sensor selbst jede Minute. Das ist umgesetzt, aber erst mit Ticket 10 per Szenario testbar; bitte dort mit abdecken.

**Logbuch:** Bei jeder Änderung der Solltemperatur feuert der Room Controller das Ereignis `climate_control_target_changed`. `logbook.py` beschreibt es am Raum-Thermostat, z. B. „Wohnzimmer 21,5 °C (Komfort bis 09:00)“. Kein Eintrag beim ersten Bewerten nach einem Neustart und keiner, wenn sich nur der Grund ändert (z. B. Heizen mit aktuellem Sollwert). Beim Neuladen des Eintrags (Optionsänderung) wird gegen den Sollwert vor dem Neuladen verglichen, eine geänderte Komfort-Temperatur erscheint also genau einmal.

**Zur Entscheidung (Logbuch-Rauschen):** Home Assistant schreibt jede Zustandsänderung eines Text-Sensors ins Logbuch. Neben dem Sollwert-Eintrag erscheint deshalb auch „Grund wechselte zu …“. Bei „Fenster offen seit N min“ (Spec-Wortlaut) wäre das ein Eintrag pro Minute, solange das Fenster offen ist. Saubere Abhilfe gibt es nur über einen festen Text, z. B. „Fenster offen seit 14:03“. Umgesetzt ist der Spec-Wortlaut. Falls das Rauschen stört, bitte in Ticket 10 auf die Uhrzeit umstellen (nur Übersetzung und Parameterformat).

**Diagnose:** `settings` (globale Optionen, `persons` und `notify_targets` geschwärzt), pro Raum `settings` (Subentry-Daten), `snapshot` (letzter `RoomSnapshot`, generisch serialisiert, neue Felder erscheinen automatisch) und `decisions` (die letzten 20 unterschiedlichen Entscheidungen seit dem letzten Laden des Eintrags, mit Zeitpunkt).

**Offen:** Die Spec nennt „Grund“ auch als Attribut des Raum-Thermostats. Das ist hier nicht umgesetzt (das Ticket verlangt nur den Sensor). Ob Text oder Code gemeint ist, bitte bei Bedarf festlegen.

**Tests:** `tests/test_reason.py` (Komfort, Nacht, Eco mit Datum, Übersteuerung, Aus, Abwesend, Englisch, Sprachwechsel, Texte aller Codes in beiden Sprachen), `tests/test_logbook.py` (echtes Logbuch mit In-Memory-Recorder; `frontend` wird nur als geladen markiert), `tests/test_diagnostics.py` (Download über die HTTP-API). Websocket- und HTTP-Clients brauchen ein Token, das nicht in der Zukunft ausgestellt ist. Deshalb öffnen die Tests die Verbindung vor dem Zurückstellen der Uhr bzw. stellen das Token zur Testzeit aus.
