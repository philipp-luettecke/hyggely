# 17: Panel-Gerüst mit Raumübersicht

Spec: `.scratch/heating-control/spec.md`

**What to build:** Die Integration registriert in der Seitenleiste den Eintrag „Heizung“, der nur für Admins sichtbar ist, und liefert das Heating Panel als JavaScript-Modul aus. Das Panel zeigt für das Handy optimiert alle Räume mit Ist-Temperatur, Solltemperatur, Modus und Grund und aktualisiert sich live. Antippen einer laufenden Übersteuerung oder von Aus setzt den Raum auf Auto zurück. Das Panel spricht nur mit der Panel API der Integration und enthält keine Heizlogik. Interne `ha-*`-Komponenten des Frontends setzt es nicht voraus. Gestaltung laut Rückmeldung aus Ticket 16.

**Blocked by:** 05, 06, 16

**Status:** ready-for-agent

- [ ] Der Seitenleisten-Eintrag „Heizung“ erscheint nach dem Einrichten der Integration nur für Admins
- [ ] Die Panel API liefert eine Raumübersicht und meldet Änderungen per Abonnement. Für Nicht-Admins ist sie gesperrt
- [ ] Das Panel zeigt alle Räume mit Ist, Soll, Modus und Grund und aktualisiert sich ohne Neuladen
- [ ] Antippen beendet Übersteuerung oder Aus über die Panel API
- [ ] Das Panel funktioniert in der Home-Assistant-App auf iOS und Android
- [ ] Der Build des Panels ist in die automatischen Prüfungen integriert
- [ ] Tests im Test-Home-Assistant decken die Panel API ab, das Panel selbst ist per Checkliste auf dem Handy abgenommen
