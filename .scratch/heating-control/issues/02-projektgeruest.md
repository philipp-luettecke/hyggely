# 02: Projektgerüst

Spec: `.scratch/heating-control/spec.md`

**What to build:** Die Integration lässt sich in Home Assistant 2026.11 installieren und über die Oberfläche einrichten. Der Einrichtungsdialog legt den Haupteintrag mit den globalen Einstellungen an: Personen, Abwesend-Verzögerung, Benachrichtigungsempfänger, Ruhezeit, Temperaturen für Abwesend, Urlaub und Frostschutz, Standard-Rückfallregel und Fenster-Verzögerung. Diese Einstellungen lassen sich im Optionsdialog ändern. Das Repository ist HACS-/Marketplace-kompatibel. Formatierung, Typprüfung und Tests laufen automatisch, und der Test-Home-Assistant ist für alle Folgetickets nutzbar.

**Blocked by:** None (can start immediately)

**Status:** done

- [ ] Die Integration erscheint unter „Integration hinzufügen“ und lässt sich ohne YAML einrichten
- [ ] Der Haupteintrag kann nur einmal angelegt werden, und alle globalen Einstellungen sind im Optionsdialog änderbar
- [ ] Die Standardwerte aus der Spec sind vorbelegt (Rückfall `earliest` mit 3 h, Abwesend-Verzögerung 30 min, Fenster-Verzögerung 60 s, Ruhezeit 22–7 Uhr)
- [ ] Die Oberflächentexte gibt es auf Deutsch und Englisch
- [ ] Lint, Typprüfung und Tests laufen lokal mit einem Befehl und in der CI
- [ ] Ein Test richtet die Integration im Test-Home-Assistant ein und prüft, dass der Haupteintrag geladen ist
- [ ] Es gibt eine wiederverwendbare Test-Hilfe für simulierte TRVs (Zustand setzen, `climate`-Aufrufe abfangen) als Grundlage für Ticket 03

## Comments

**Benachrichtigungsempfänger (für Ticket 14):** Die Empfänger sind `notify`-Entitäten (Entitätsauswahl, Domäne `notify`, mehrfach), gespeichert als Liste von Entity-IDs unter `notify_targets` in den Optionen des Haupteintrags. Versand später über `notify.send_message` mit `entity_id` = diese Liste sowie `title` und `message`. Begründung: Die Companion App (`mobile_app`) legt in HA 2026.11 pro Handy eine `notify`-Entität an; das ist der aktuelle, auswählbare Weg. Alte `notify.<dienst>`-Aktionen (z. B. für `data`/actionable notifications) werden bewusst nicht unterstützt. Brauchen wir das später, ergänzen wir es in Ticket 14.

**Test-Paket:** Die Spec nennt `pytest-homeassistant-custom-component`. Davon gibt es kein Release für HA 2026.11 (letztes: 0.13.375 für 2026.10.4), und das Projekt verweist selbst auf den Nachfolger. Verwendet wird deshalb das offizielle Paket `pytest-homeassistant==2026.11.2` aus HA Core (Version = HA-Version, pinnt `homeassistant==2026.11.2`). Die Test-Schnittstelle bleibt dieselbe: die Integration in einem echten Test-Home-Assistant.

**Standardwerte für Temperaturen:** Die Spec nennt keine Standardwerte für Abwesend, Urlaub und Frostschutz. Vorbelegt sind 17 °C, 15 °C und 7 °C (TRV-Bereich 5–25 °C, Schrittweite 0,5 °C). Bitte bei Bedarf anpassen.

**Speicherort:** Alle globalen Einstellungen liegen in den `options` des Haupteintrags (`data` bleibt leer), damit Einrichtung und Optionsdialog dieselben Werte bearbeiten. Dauern sind im Format des Dauer-Selektors gespeichert (`{"hours", "minutes", "seconds"}`), Uhrzeiten als `"HH:MM:SS"`.

**Simulierte TRVs:** `tests/simulated_trv.py`, Fixture `simulated_trvs`. Jedes TRV ist eine echte `climate`-Entität auf eigenem Gerät, gesteuert über die normalen `climate.*`-Aktionen. Aufrufe werden mitgeschrieben (`trv.calls`) und sofort übernommen (abschaltbar mit `trv.apply_commands = False`). `trv.report(...)` simuliert vom TRV gemeldete Werte mit neuem Context. Für Ticket 08/13 zu ergänzen: Minutentakt der Abfrage, Ignorieren einer Temperatur ohne Modus im Zustand `off`, Einfrieren bei Bridge-Ausfall samt Temperatursensor am selben Gerät.

**WSL-Umgebung:** In `RSLinux-24.04` ist die DNS-Auflösung kaputt (WSL-Resolver `10.255.255.254` verweigert Verbindungen). TLS ist in Ordnung. Details und Umgehung ohne Abschalten der TLS-Prüfung stehen in `AGENTS.md`. Dauerhafte Lösung braucht sudo (siehe dort).

**Abgeschlossen:** Merge-Commit `9f71501` auf `feat/heating-control`. Ergebnis: Integration `climate_control` mit Haupteintrag, Optionsdialog, DE/EN-Texten, Test-Hilfe für simulierte TRVs und `wsl -d RSLinux-24.04 -- ./scripts/check` (Lint, mypy, 14 Tests grün).
