# 17: Panel-Gerüst mit Raumübersicht

Spec: `.scratch/heating-control/spec.md`

**What to build:** Die Integration registriert in der Seitenleiste den Eintrag „Heizung“, der nur für Admins sichtbar ist, und liefert das Heating Panel als JavaScript-Modul aus. Das Panel zeigt für das Handy optimiert alle Räume mit Ist-Temperatur, Solltemperatur, Modus und Grund und aktualisiert sich live. Antippen einer laufenden Übersteuerung oder von Aus setzt den Raum auf Auto zurück: ohne Nachfrage, mit 6 Sekunden „Rückgängig“. Das Panel sendet das Beenden erst nach Ablauf dieser 6 Sekunden, beim Verlassen des Panels sofort. Ein Tipp auf einen Raum in Auto bewirkt in diesem Ticket nichts (Sprung zum Zeitplan in Ticket 18). Während der Vorlaufzeit nennt der Grund das Vorheizen („Vorheizen auf Komfort, Beginn 16:30“) statt „Komfort bis 22:00“. Das Panel spricht nur mit der Panel API der Integration und enthält keine Heizlogik. Interne `ha-*`-Komponenten des Frontends setzt es nicht voraus. Gestaltung laut Rückmeldung aus Ticket 16.

**Blocked by:** 05, 06, 16

**Status:** ready-for-agent

- [ ] Der Seitenleisten-Eintrag „Heizung“ erscheint nach dem Einrichten der Integration nur für Admins
- [ ] Die Panel API liefert eine Raumübersicht und meldet Änderungen per Abonnement. Für Nicht-Admins ist sie gesperrt
- [ ] Das Panel zeigt alle Räume mit Ist, Soll, Modus und Grund und aktualisiert sich ohne Neuladen
- [ ] Antippen beendet Übersteuerung oder Aus über die Panel API, ohne Nachfrage
- [ ] Nach dem Antippen bietet das Panel 6 Sekunden lang „Rückgängig“. Der Befehl geht erst danach raus (beim Verlassen des Panels sofort), Rückgängig verwirft ihn
- [ ] Während der Vorlaufzeit liefert der Grund-Sensor den neuen Grund-Code `preheat` mit Stufe und Blockbeginn („Vorheizen auf Komfort, Beginn 16:30“). Ab Blockbeginn gilt wieder „Komfort bis …“
- [ ] Das Panel funktioniert in der Home-Assistant-App auf iOS und Android
- [ ] Der Build des Panels ist in die automatischen Prüfungen integriert
- [ ] Tests im Test-Home-Assistant decken die Panel API und den Grund `preheat` ab, das Panel selbst ist per Checkliste auf dem Handy abgenommen

## Comments

**Rückmeldung aus Ticket 16 (25.11.2026):** Fragen 4 und 8. Die Reiter (vier wie im Prototyp oder drei: Übersicht, Räume, Haus) sind noch offen (Ticket 16, Frage 12); das Gerüst legt die Reiter laut dieser Entscheidung an.
