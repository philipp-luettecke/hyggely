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

**Umbenennung in Hyggely, Lizenz, Markenbild:** Merge-Commit `d8113e9` auf `feat/heating-control` (Branch `ticket/21-hyggely`), `scripts/check` grün (281 Tests), hassfest von Home Assistant 2026.11.2 lokal gegen `custom_components/hyggely`: 0 ungültige Integrationen. Entscheidungen des Admins zu den offenen Punkten 1–4 oben sind damit umgesetzt.
- **Name:** Anzeigename „Hyggely“, Domain `hyggely`. Ordner `custom_components/hyggely` (per `git mv`), Service `hyggely.start_vacation`, Websocket-Befehle `hyggely/...`, Panel unter `/hyggely` mit Element `hyggely-panel`, Modul unter `/hyggely/frontend/heating-panel.js`, Hersteller der Geräte und Titel des Haupteintrags „Hyggely“, `hacs.json`, `pyproject.toml` (Projekt `hyggely`), `uv.lock`, `frontend/package.json`, Skripte (Cache jetzt `~/.cache/hyggely`), README, CHANGELOG, `AGENTS.md`, Spec (nur der Servicename). Seitenleisten-Titel „Heizung“ und die Begriffe aus `GLOSSARY.md` bleiben. Unique IDs hatten nie ein Domain-Präfix; Geräte-Identifier und Speicher-Schlüssel folgen `DOMAIN`. Keine Migration: Hyggely ist für Home Assistant eine neue Integration. `climate_control` steht nur noch in historischen Texten unter `.scratch/`, auch im Häkchen oben zum Service, das jetzt `hyggely.start_vacation` meint.
- **Repository und Manifest:** `documentation` `https://github.com/philipp-luettecke/hyggely`, `issue_tracker` `…/issues`, `codeowners` `["@philipp-luettecke"]`. Kein Remote angelegt.
- **Lizenz:** `LICENSE` ist der offizielle Text von apache.org, unverändert (SHA-256 `cfc7749b…3d30`); die Copyright-Zeile „Copyright 2026 Philipp Lüttecke“ steht in `NOTICE`. `pyproject.toml` mit `license = "Apache-2.0"`, Abschnitt „License“ in der README.
- **Markenbild:** `brand/icon.png` (256×256) und `brand/icon@2x.png` (512×512) aus Logo-Entwurf B, Ecken außerhalb der abgerundeten Kachel transparent (Radius aus dem Entwurf gemessen, kantengeglättet), verlustfrei optimiert (46 KB bzw. 204 KB; die Größe kommt vom feinen Rauschen der dunklen Kachel im Entwurf). Laut Doku zu Brand-Bildern (seit HA 2026.3) fällt ein fehlendes Logo auf das Icon zurück, und bei quadratischem Logo genügt das Icon, darum kein `logo.png`. Die README zeigt das Icon oben. In der CI ist die HACS-Prüfung `brands` wieder an; die Prüfung `license` ist jetzt erfüllt.

**Offen für den Admin:**
1. **Sichtbarkeit des Repositorys:** Marketplace (früher HACS) installiert nur aus **öffentlichen** GitHub-Repositories, auch als benutzerdefiniertes Repository; die HACS-Validierung prüft dann ebenfalls ein öffentliches Repo. Optionen: A öffentlich anlegen (Installation und Updates über den Marketplace), B privat lassen und von Hand installieren (Ordner `custom_components/hyggely` kopieren, Updates von Hand), C erst privat, vor dem Release öffentlich. Empfehlung A oder C.
2. **Repo anlegen und pushen:** `philipp-luettecke/hyggely` anlegen, Issues aktivieren, Beschreibung und Topics setzen, Remote `origin` eintragen und `feat/heating-control` pushen; danach `description topics` aus `ignore` in `.github/workflows/ci.yml` streichen.
3. **CI grün:** Checks, hassfest (`@master`, evtl. neuer als 2026.11.2) und HACS-Validierung.
4. **Release `0.1.0`:** Tag `0.1.0`, GitHub-Release mit den Notizen aus `CHANGELOG.md` (Datum eintragen).
5. **Neueinrichtung und Handy-Abnahme:** Die alte Integration „Climate Control“ entfernen (Eintrag löschen, Ordner `custom_components/climate_control` löschen), neu starten, Hyggely installieren und Haupteintrag und Räume neu anlegen; Automationen mit `climate_control.start_vacation` auf `hyggely.start_vacation` umstellen. Dann die Abnahme der Tickets 17–20 auf dem Handy, Häkchen setzen und das Ticket schließen.
