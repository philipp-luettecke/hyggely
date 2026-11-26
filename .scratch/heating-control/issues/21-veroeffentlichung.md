# 21: Veröffentlichung

Spec: `.scratch/heating-control/spec.md`

**What to build:** Die Integration ist für den Alltag und für eine Veröffentlichung bereit.
- Die Installationsanleitung beschreibt die Einrichtung von Haupteintrag und Räumen.
- Der Einrichtungsdialog weist darauf hin, an HomeKit-Bridge und Google nur die Raum-Thermostate und nicht die TRVs freizugeben.
- Die Anleitung erklärt, wie man das in der HomeKit-Bridge und beim Google Assistant ohne Nabu Casa einstellt.
- Die Repository-Metadaten für HACS/Marketplace sind vollständig, und es gibt ein erstes Release.

**Blocked by:** 09, 14, 18, 19, 20

**Status:** ready-for-human

- [ ] Die Installationsanleitung deckt Installation, Haupteintrag, Räume, Zeitpläne und Panel ab, inklusive Raum ohne Zeitplan (hält Eco, Zeitplan im Panel anlegen) und des Service `climate_control.start_vacation`
- [ ] Der Einrichtungsdialog eines Raums zeigt den Hinweis zur Freigabe an HomeKit-Bridge und Google
- [ ] Die Anleitung beschreibt das Ausschließen der TRVs und das Freigeben der Raum-Thermostate in der HomeKit-Bridge
- [ ] Die Anleitung beschreibt das Freigeben der Raum-Thermostate an Google Assistant ohne Nabu Casa
- [ ] Die Validierung für HACS/Marketplace und die von Home Assistant für Integrationen laufen grün
- [ ] Ein versioniertes Release mit Änderungsnotizen existiert

## Comments

**Lokal umgesetzt:** Merge-Commit `3b7f416` auf `feat/heating-control` (Branch `ticket/21-veroeffentlichung`), `scripts/check` grün (281 Tests).
- **Anleitung** in `README.md` (Englisch wie die übrige Doku, Oberflächenbegriffe deutsch in Klammern): Installation per HACS (benutzerdefiniertes Repository) und von Hand, Haupteintrag mit Standardwerten, Räume, Zeitpläne (Stufe `level` in den Zusatzdaten), Raum ohne Zeitplan (hält Eco, „Zeitplan anlegen“ im Panel), Bedienung, Panel „Heizung“ nur für Admins, Hausbetriebsart/Urlaub/Abwesend, Service `climate_control.start_vacation` mit Beispiel, Grund-Codes, Benachrichtigungen. Abschnitte HomeKit-Bridge (Optionsdialog: Modus bridge, Einschlussmodus include, Domäne Climate, nur Raum-Thermostate wählen; YAML-Filter `include_entities`) und Google Assistant ohne Nabu Casa (manuelle Einrichtung laut HA-Doku, `expose_by_default: false` plus `entity_config … expose: true`, `google_assistant.reload`, Sync). Grundlage: aktuelle Doku auf home-assistant.io und `homekit/strings.json` bzw. `homekit/__init__.py` in Core (versteckte Entitäten werden nur bei ausdrücklicher Auswahl freigegeben).
- **Hinweis im Einrichtungsdialog:** Der Schritt „Raum hinzufügen“ nennt jetzt HomeKit-Bridge und Google Assistant: nur die Raum-Thermostate freigeben, nicht die Heizkörperthermostate (DE/EN, `strings.json`). Test `test_adding_a_room_asks_to_share_only_room_thermostats` öffnet den Dialog im Test-Home-Assistant und prüft den Text in beiden Sprachen. Der Dialog „Raum ändern“ bekommt keinen Hinweis (Ticket nennt nur den Einrichtungsdialog).
- **hassfest-Befund behoben:** hassfest lehnte die Grund-Texte mit Platzhaltern (`{until}`, `{since}`, `{level}`, `{start}`) unter `entity.sensor.reason.state` ab; die CI wäre rot gewesen. Alle Grund-Texte liegen jetzt unter `common` als `reason_<code>[_until|_since|_start]` (wie die Benachrichtigungstexte aus Ticket 14), `reason_text.py` liest von dort. Verhalten unverändert; `tests/test_reason.py` prüft den neuen Ort.
- **Validierung:** hassfest von Home Assistant 2026.11.2 lokal aus dem Core-Quellcode im Test-Virtualenv: 0 Fehler, 0 Warnungen (Docker kann hier nur Windows-Container, Vorgehen in `AGENTS.md`). Die CI nutzt `hassfest@master`, also eine evtl. neuere Fassung. Die HACS-Validierung braucht das GitHub-Repository und lief nicht lokal; von Hand geprüft: `hacs.json` (`name`, `homeassistant`), Manifest-Schlüssel für HACS und hassfest inkl. Sortierung, Kategorie `climate.thermostats_heating` existiert in Core, Abhängigkeiten `frontend`, `http`, `panel_custom`, `websocket_api` und Importe passen zu den hassfest-Regeln, `services.yaml` passt zum Schema, Texte in `translations/en.json`.
- **Version 0.1.0** (steht schon im Manifest): erstes Release, 0.x, weil die Abnahme des Panels auf dem Handy (17–20) noch aussteht und sich nach dem Sichten durch den Haushalt noch ändern kann. Änderungsnotizen in `CHANGELOG.md` („not released yet“). Tag = Manifest-Version (`0.1.0`), wie es die Marketplace-Anleitung empfiehlt. Kein Release-Zip: Das Panel-Modul ist eingecheckt und von `scripts/panel check` abgesichert (offene Frage aus Ticket 17).

**Offen für den Admin (vor bzw. nach dem Push):**
1. **GitHub-Repository:** Besitzer und Name bestätigen. `documentation` und `issue_tracker` im Manifest zeigen seit Ticket 02 auf `https://github.com/luetteck/climate-control` (nicht geprüft). Repository öffentlich anlegen, Issues aktivieren, Beschreibung und Topics setzen, dann `description topics` aus `ignore` in `.github/workflows/ci.yml` streichen.
2. **Codeowner:** GitHub-Benutzername für `codeowners` (heute `[]`; laut HA-Doku „mindestens du selbst“).
3. **Lizenz:** Es gibt keine `LICENSE`. Die HACS-Prüfung `license` ist in der CI nicht ausgeschaltet und schlägt ohne OSI-Lizenz fehl. Optionen: A Apache-2.0 (wie Home Assistant Core), B MIT, C GPL-3.0. Empfehlung A. Ob veröffentlicht werden darf, entscheidet der Admin.
4. **Markenbild:** HACS verlangt `custom_components/climate_control/brand/icon.png` (256×256, kein Home-Assistant-Logo); die Prüfung `brands` ist in der CI ausgeschaltet. Optionen: A schlichtes Heizkörper-Symbol (z. B. `mdi:radiator`, Apache-2.0), B eigenes Logo, C vorerst ohne. Empfehlung A.
5. **Nach dem Push:** CI (Checks, hassfest, HACS) grün, dann GitHub-Release `0.1.0` mit den Notizen aus `CHANGELOG.md` (Datum eintragen). Danach Häkchen setzen und das Ticket schließen.
