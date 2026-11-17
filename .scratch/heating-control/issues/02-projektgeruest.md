# 02: Projektgerüst

Spec: `.scratch/heating-control/spec.md`

**What to build:** Die Integration lässt sich in Home Assistant 2026.11 installieren und über die Oberfläche einrichten. Der Einrichtungsdialog legt den Haupteintrag mit den globalen Einstellungen an: Personen, Abwesend-Verzögerung, Benachrichtigungsempfänger, Ruhezeit, Temperaturen für Abwesend, Urlaub und Frostschutz, Standard-Rückfallregel und Fenster-Verzögerung. Diese Einstellungen lassen sich im Optionsdialog ändern. Das Repository ist HACS-/Marketplace-kompatibel. Formatierung, Typprüfung und Tests laufen automatisch, und der Test-Home-Assistant ist für alle Folgetickets nutzbar.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Die Integration erscheint unter „Integration hinzufügen“ und lässt sich ohne YAML einrichten
- [ ] Der Haupteintrag kann nur einmal angelegt werden, und alle globalen Einstellungen sind im Optionsdialog änderbar
- [ ] Die Standardwerte aus der Spec sind vorbelegt (Rückfall `earliest` mit 3 h, Abwesend-Verzögerung 30 min, Fenster-Verzögerung 60 s, Ruhezeit 22–7 Uhr)
- [ ] Die Oberflächentexte gibt es auf Deutsch und Englisch
- [ ] Lint, Typprüfung und Tests laufen lokal mit einem Befehl und in der CI
- [ ] Ein Test richtet die Integration im Test-Home-Assistant ein und prüft, dass der Haupteintrag geladen ist
- [ ] Es gibt eine wiederverwendbare Test-Hilfe für simulierte TRVs (Zustand setzen, `climate`-Aufrufe abfangen) als Grundlage für Ticket 03
