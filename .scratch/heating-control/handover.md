# Handover: Heating Panel (Tickets 17–21)

Stand: 25.11.2026, Integrationsbranch `feat/heating-control` (nicht gepusht). Tickets 01–16 sind `done`, offen sind 17–21. Dieses Dokument ist der Einstieg für mehrere parallel arbeitende Agenten. Es verweist auf die Quellen, statt sie zu wiederholen; bei Widerspruch gelten die Tickets.

## Pflichtlektüre für jeden Agenten

1. `AGENTS.md`: Checks (`wsl -d RSLinux-24.04 -- ./scripts/check`), Git nur unter Windows, WSL-DNS-Workaround.
2. `.scratch/heating-control/spec.md`: vor allem Module 9 (Panel API) und 10 (Heating Panel) mit „Gestaltung laut Abnahme“, Testing Decisions, Further Notes.
3. `GLOSSARY.md`: verbindliche Begriffe für Code, Tests und Oberfläche.
4. Das eigene Ticket unter `.scratch/heating-control/issues/` und **Ticket 16, `## Comments`**: alle zwölf Gestaltungsentscheidungen mit Begründung.
5. `docs/agents/issue-tracker.md`: Status-Werte, Kommentare unter `## Comments`.

Skills: `implement-spec` (Orchestrierung mehrerer Agenten), `implement` bzw. `tdd` (ein Ticket), `code-review` (am Ende).

## Stand der Tickets

| Ticket | Status | Blockiert durch | Kern |
|---|---|---|---|
| 17 Panel-Gerüst mit Raumübersicht | ready-for-agent, **frei** | – (05, 06, 16 done) | Seitenleiste, Panel API, Übersicht, drei Reiter, Grund-Code `preheat` |
| 18 Wochenraster, Zeitplan anlegen/zuweisen | ready-for-agent | 17 | Raumseite: Zeitleiste (Variante B), Kopieren, Abtrennen, Löschen; Zeitplan optional, Grund-Code `no_schedule` |
| 19 Stufen und Vorlaufzeit | ready-for-agent | 17 | Raumseite: Stufen/Vorlaufzeit; Reiter Haus: globale Temperaturen; `TEMPERATURE_STEP` = 1 °C |
| 20 Hausbetriebsart und Urlaub | ready-for-agent | 17 | Reiter Haus: Betriebsart, Urlaub mit Ende, Personen; Service `climate_control.start_vacation` |
| 21 Veröffentlichung | ready-for-agent | 09, 14, 18, 19, 20 | Anleitung, Hinweis im Einrichtungsdialog, HACS, Release |

## Ablauf und Parallelisierung

- **Welle 1: Ticket 17 allein.** Es legt alles an, worauf 18–20 aufbauen: Frontend-Build, Auslieferung als Modul, Registrierung des Panels, Websocket-Modul der Panel API, Abonnement der Raumübersicht, Reiter-Gerüst.
- **Welle 2: Tickets 18, 19 und 20 parallel**, sobald 17 in `feat/heating-control` gemergt ist.
- **Welle 3: Ticket 21**, nach 18–20.
- **Optional, nur nach Rücksprache mit dem Admin:** Die reinen Integrationsteile ohne Panel könnten schon parallel zu 17 laufen. Das sind `no_schedule` und der optionale Zeitplan aus 18, `TEMPERATURE_STEP` aus 19 und der Service aus 20. Formal sind sie durch 17 blockiert. Wer sie vorzieht, sollte sie als eigene Teil-Branches führen und im Ticket kommentieren.

**Aufgabe von Ticket 17 für die Parallelität:** Das Gerüst muss Nahtstellen anlegen, damit 18, 19 und 20 nicht dieselben Dateien ändern.
- Die Raumseite unter „Räume“ bekommt einen Abschnitt für Zeitplan und Zuweisung (18) und einen für Stufen und Vorlaufzeit (19).
- Der Reiter „Haus“ bekommt einen Abschnitt für Betriebsart, Urlaub und Abwesend (20) und einen für die globalen Temperaturen (19).
- Die Panel API registriert ihre Websocket-Befehle so, dass jedes Ticket eigene Befehle in einer eigenen Datei oder einem eigenen Block ergänzt.
- Die Abschnitte dürfen in 17 leer oder Platzhalter sein. Wie 17 die Nahtstellen anlegt, bitte im Abschlusskommentar von 17 festhalten.

**Konfliktstellen in Welle 2**, die beim Mergen mit `feat/heating-control` zu beachten sind:
- `strings.json` und `translations/de.json`, `translations/en.json`: 18 (Grund `no_schedule`, Einrichtungsdialog), 20 (Service). Den Grund `preheat` bringt 17.
- `const.py`: 19 (`TEMPERATURE_STEP`), eventuell 18.
- `target_resolver.py`, `schedule_reader.py`, `room_controller.py`, `reason_text.py`: 17 (`preheat`) und 18 (`no_schedule`, Auswertung ohne Zeitplan).
- `config_flow.py`: 18 (Zeitplan optional), 19 (Schrittweite über `TEMPERATURE_STEP`).

## Arbeitsweise (wie bei den Tickets 01–16)

- **Ein Ticket, ein Branch, ein Worktree:** Branch `ticket/NN-<slug>`, z. B. `ticket/17-panel-geruest`, Worktree unter `.worktrees/` (ignoriert). Basis ist die aktuelle Spitze von `feat/heating-control`. Git nur unter Windows ausführen, im Worktree funktioniert Git in WSL nicht.
- **Testgetrieben** mit dem Skill `tdd` an der einzigen Test-Schnittstelle, also dem Test-Home-Assistant über `pytest-homeassistant`, Fixture `simulated_trvs` aus `tests/simulated_trv.py`. Für das Panel gibt es keine automatischen Oberflächentests; die Abnahme läuft per Checkliste auf dem Handy und wird als Kommentar im Ticket abgelegt.
- **Vor dem Melden:** die Spitze von `feat/heating-control` in den eigenen Branch mergen, dann `wsl -d RSLinux-24.04 -- ./scripts/check` grün.
- **Abschluss:** Merge nach `feat/heating-control` als „Merge ticket NN: <Ergebnis>“. Im Ticket unter `## Comments` einen Kommentar „**Abgeschlossen:** Merge-Commit `<sha>` … Ergebnis: …“ ergänzen, `**Status:** done` setzen und als „Close ticket NN“ committen. Rückfragen kommen als `needs-info` mit konkreten Optionen und einer Empfehlung ins Ticket (Vorbild: Ticket 04).
- **Nicht pushen**, außer der Admin sagt es ausdrücklich.

## Fakten, die Agenten sonst selbst suchen müssten

- **Noch kein Frontend im Repo:** Es gibt kein `package.json`, und die CI (`.github/workflows/ci.yml`) kennt nur Python, hassfest und HACS. Die Wahl des Build-Werkzeugs trifft Ticket 17. Vorgaben: Das Panel ist ein ausgeliefertes JavaScript-Modul, setzt keine internen `ha-*`-Komponenten voraus, und der Build läuft in den automatischen Prüfungen (also in `scripts/check` und in der CI).
  - Node in WSL ist 18.19.1 mit npm 9.2.0, unter Windows Node 24. In der CI braucht es `setup-node`.
  - Ein `npm install` in WSL scheitert vermutlich an derselben DNS-Sperre wie `uv sync`. Der Workaround mit `unshare` aus `AGENTS.md` gilt sinngemäß.
  - Für die Prüfungen am besten das gebaute Modul einchecken oder reproduzierbar bauen; die Entscheidung bitte in Ticket 17 festhalten.
- **Zeitpläne:** Das Panel liest, schreibt und löscht sie nur über die nativen Websocket-Befehle `schedule/list`, `schedule/create`, `schedule/update` und `schedule/delete` (nur für Admins). Die Stufe steht in den Zusatzdaten des Blocks unter `data.level` (`night`; fehlt die Angabe, gilt Komfort), siehe `schedule_reader.py`. Die Integration selbst kann keine Helfer anlegen.
- **Raum ohne Zeitplan (18):** Heute ist `CONF_SCHEDULE` in `config_flow.py` ein Pflichtfeld. Liefert `ScheduleReader.read()` `None`, bricht `RoomController._async_evaluate` ab, und der Raum behält den letzten Sollwert, selbst bei offenem Fenster. Ziel laut Ticket: Eco mit Grund-Code `no_schedule`, alle übrigen Regeln wirken weiter.
- **Vorlaufzeit (17):** Die Regel aus Ticket 04 gilt: Vorgeheizt wird nur auf eine strikt wärmere Stufe. Neu ist nur der Grund während der Vorlaufzeit: „Vorheizen auf Komfort, Beginn 16:30“, Code `preheat`. Die vorhandenen Grund-Texte stehen unter `entity.sensor.reason.state` in `translations/de.json`.
- **Schrittweite (19):** `TEMPERATURE_STEP` (`const.py`) wirkt auf den Einrichtungs- und Optionsdialog und auf `_attr_target_temperature_step` in `climate.py`. Mehrere Tests nutzen halbe Grad (z. B. `test_room_follows_schedule.py`, `test_levels_and_lead_time.py`, `test_away.py`); prüfen, welche Tests betroffen sind.
- **Urlaub (20):** `HouseModeController` in `house_mode.py` mit `async_set_house_mode` und `async_set_vacation_end`. Ohne Urlaubsende in der Zukunft wird Urlaub mit `ServiceValidationError` (`vacation_end_not_ahead`) abgelehnt (Ticket 12, Kommentare). Der neue Befehl der Panel API und der Service setzen beides in einem Schritt.
- **Personen (20):** Die Abwesenheit kommt aus `presence.py`. Eine unbekannte oder nicht erreichbare Person zählt als zu Hause.

## Prototyp als Vorlage

- Branch `prototype/15-panel`, Commit `d86014b`, **nie mergen**. Datei `prototypes/heating-panel/heating-panel-prototype.html`. Ansehen ohne Branchwechsel: `cmd /c "git show prototype/15-panel:prototypes/heating-panel/heating-panel-prototype.html > %TEMP%\hp.html"` und dann im Browser öffnen.
- Maßgeblich ist die Aufteilung „3R“ (`?layout=3`) mit Variante B (Standard). `?selftest=1` führt einen Selbsttest aus.
- Der Prototyp zeigt **nicht**: Block kopieren, den Hinweis über Mitternacht, „Rückgängig“ mit verzögertem Senden, `preheat`, 1-°C-Schritte, den Hinweis bei vertauschten Stufen, Urlaub erst nach Wahl des Endes, die Personenliste und „Löschen / Behalten“. Er rechnet außerdem noch mit der alten Vorlaufzeit-Regel. Dafür gelten die Tickets.

## Auftrag für einen Orchestrator-Agenten

> Setze die Tickets 17 bis 21 aus `.scratch/heating-control/issues/` auf dem Integrationsbranch `feat/heating-control` um, mit dem Skill `implement-spec`. Einstieg: `.scratch/heating-control/handover.md`. Arbeite im Hauptcheckout `C:\Users\luetteck\climate-control`, Implementierer in eigenen Worktrees unter `.worktrees/`. Starte mit Ticket 17 allein, danach 18, 19 und 20 parallel, zuletzt 21. Nicht pushen. Antworte auf Deutsch.

## Auftrag für einen Implementierer-Agenten (pro Ticket)

> Setze Ticket NN aus `.scratch/heating-control/issues/NN-<slug>.md` um, mit dem Skill `tdd`. Lies zuerst `.scratch/heating-control/handover.md` und die dort genannte Pflichtlektüre. Lege den Branch `ticket/NN-<slug>` in einem Worktree unter `.worktrees/` an, mit Basis auf der aktuellen Spitze von `feat/heating-control`. Merge vor dem Abschluss die Spitze von `feat/heating-control`, lass `./scripts/check` grün laufen, merge nach `feat/heating-control` und schließe das Ticket wie im Handover beschrieben. Bei offenen Gestaltungsfragen: Ticket auf `needs-info` setzen, Optionen mit Empfehlung kommentieren und nachfragen, nicht raten. Nicht pushen. Antworte auf Deutsch.
