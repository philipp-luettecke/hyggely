# 18: Panel: Wochenraster bearbeiten, Zeitplan anlegen und zuweisen

Spec: `.scratch/heating-control/spec.md`

**What to build:** Im Reiter „Räume“ des Heating Panel wählt der Admin einen Raum über Raum-Chips. Die Raumseite zeigt oben die Zuweisung des Zeitplans und darunter den Zeitplan des Raums. Die Woche erscheint als Mini-Leiste pro Tag mit Stufenfarben, ein Tag wird als Zeitleiste bearbeitet (Variante B aus Ticket 16). Der Admin kann Blöcke anlegen, an Griffen verlängern und kürzen, als Ganzes verschieben und löschen und ihnen eine Stufe (Komfort oder Nacht) zuweisen. Jedes Ziehen wird sofort gespeichert. Ein Block lässt sich auf andere Tage kopieren, ein ganzer Tag mit „Tag kopieren nach …“ (Schnellwahl Mo–Fr, Sa–So, Alle). Blöcke über Mitternacht bleiben zwei Blöcke, am Tagesrand steht ein Hinweis auf das Gegenstück. Ein Tipp auf einen Raum in Auto in der Übersicht öffnet seine Raumseite mit dem heutigen Tag.

Gilt der Zeitplan des Raums auch für andere Räume, zeigt die Raumseite „gilt auch für …“, einen Hinweis, dass jede Änderung sofort auf alle wirkt, und „Für <Raum> abtrennen“ (legt eine Kopie an und weist sie diesem Raum zu). Gilt er nur für diesen Raum, entfällt diese Leiste. Die Farblegende ist immer sichtbar.

Für einen Raum kann der Admin direkt einen neuen nativen Zeitplan-Helfer anlegen lassen (Vorlagen „Standardwoche“, „Leer“, „Kopie von …“, Name „Heizung <Raum>“) und ihn dem Raum zuweisen. Bei der Zuweisung sind alle Zeitplan-Helfer wählbar. Ein Zeitplan lässt sich auch mehreren Räumen zuweisen. Verliert ein Zeitplan seinen letzten Raum, bietet das Panel einmal an, ihn zu löschen. Zeitpläne werden ausschließlich über die native Zeitplan-Schnittstelle von Home Assistant gelesen, geschrieben und gelöscht.

Damit ein neuer Raum ohne vorher angelegten Helfer eingerichtet werden kann, wird der Zeitplan im Einrichtungsdialog des Raums optional. Ein Raum ohne Zeitplan, oder dessen Zeitplan-Helfer fehlt oder nicht verfügbar ist, hält Eco mit dem Grund „Kein Zeitplan – Eco“. Alle übrigen Regeln (Fenster offen, Aus, Übersteuerung, Hausbetriebsart, Abwesend) wirken weiter. Die Raumseite zeigt bei solchen Räumen statt der Zeitleiste „hält Eco“ und „Zeitplan anlegen“.

**Blocked by:** 04, 17

**Status:** ready-for-agent

- [ ] Der Reiter „Räume“ zeigt Raum-Chips. Die Raumseite enthält Zuweisung und Zeitplan des gewählten Raums
- [ ] Die Wochenübersicht zeigt alle Blöcke des Zeitplans als Mini-Leiste pro Tag mit Stufenfarben, ein gewählter Tag erscheint als Zeitleiste
- [ ] Blöcke lassen sich auf dem Handy anlegen, an Griffen verlängern und kürzen, verschieben und löschen (15-Minuten-Raster). Jede Änderung wird sofort gespeichert
- [ ] Jedem Block lässt sich eine Stufe zuweisen. Sie wird in den Zusatzdaten des Blocks gespeichert
- [ ] Ein Block lässt sich auf andere Tage kopieren, ein Tag mit „Tag kopieren nach …“ (Mo–Fr, Sa–So, Alle). Ein kopierter Tag ersetzt die Blöcke der Zieltage. Überschneidet ein kopierter Block am Zieltag einen vorhandenen, wird er dort nicht kopiert und das Panel nennt die Tage
- [ ] Blöcke bis 24:00 und ab 00:00 zeigen am Tagesrand einen Hinweis auf das Gegenstück am Nachbartag
- [ ] Ein Tipp auf einen Raum in Auto in der Übersicht öffnet seine Raumseite mit dem heutigen Tag
- [ ] Ein neuer Zeitplan-Helfer lässt sich aus dem Panel mit den Vorlagen „Standardwoche“, „Leer“ und „Kopie von …“ anlegen und einem Raum zuweisen
- [ ] Ein Zeitplan lässt sich mehreren Räumen zuweisen. Nur dann zeigt die Raumseite „gilt auch für …“, den Hinweis und „Für <Raum> abtrennen“
- [ ] Verliert ein Zeitplan seinen letzten Raum, fragt das Panel einmal „Löschen / Behalten“
- [ ] Der Zeitplan ist im Einrichtungs- und Optionsdialog des Raums optional. Ohne Zeitplan oder bei fehlendem bzw. nicht verfügbarem Helfer hält der Raum Eco mit Grund-Code `no_schedule`, und alle übrigen Regeln wirken weiter
- [ ] Änderungen wirken sofort auf die betroffenen Räume
- [ ] Mit dem Panel bearbeitete Zeitpläne bleiben im normalen Zeitplan-Editor von Home Assistant bearbeitbar
- [ ] Tests im Test-Home-Assistant decken das Zuweisen über die Panel API und den Raum ohne bzw. mit fehlendem Zeitplan ab, das Wochenraster ist per Checkliste abgenommen

## Comments

**Rückmeldung aus Ticket 16 (25.11.2026):** Fragen 1 bis 7 und 12. Vorbild ist die Raumseite der Aufteilung „3R“ im Prototyp auf `prototype/15-panel`. Hintergrund zum optionalen Zeitplan: Bisher bricht der Room Controller die Auswertung ab, wenn `ScheduleReader.read()` `None` liefert (Helfer fehlt oder ist nicht verfügbar); der Raum behält dann den letzten Sollwert, selbst bei offenem Fenster. Die Raumseite teilt sich dieses Ticket mit Ticket 19 (Stufen und Vorlaufzeit unter dem Zeitplan).

**Teil vorgezogen (Branch `ticket/18-no-schedule`):** Nur die Integrationsteile ohne Panel, nach Freigabe durch den Admin (Handover, Abschnitt „Optional“).
- Umgesetzt: Der Zeitplan ist im Einrichtungs- und Optionsdialog des Raums optional (`CONF_SCHEDULE` ist `Optional`); im Optionsdialog lässt er sich entfernen und nachträglich zuweisen. Ohne Zeitplan, oder wenn der Helfer fehlt oder nicht verfügbar ist, liefert `ScheduleReader.read()` nicht mehr `None`, sondern Eco ohne Schaltpunkt mit `ScheduleLevel.missing`; der Target Resolver entscheidet dann Eco mit dem neuen Grund-Code `no_schedule` („Kein Zeitplan – Eco“ / „No schedule – Eco“). `RoomController._async_evaluate` bricht nicht mehr ab, Fenster offen, Aus, Übersteuerung, Hausbetriebsart und Abwesend wirken weiter. Dialogtexte für Zeitplan und Eco-Temperatur nennen das Verhalten.
- Tests: `tests/test_room_without_schedule.py` (Raum ohne Zeitplan, gelöschter Helfer, Fenster offen, Übersteuerung mit Rückfall nach 3 h, Heizen ohne Temperatur, Zeitplan im Optionsdialog zuweisen und entfernen); `no_schedule` in der Übersetzungsprüfung von `tests/test_reason.py`; der Diagnose-Export zeigt `missing` im Zeitplan-Schnappschuss.
- Hinweis für den Merge mit Ticket 17 (`preheat`): Konflikte erwartet in `target_resolver.py` (`ReasonCode`, `ScheduleLevel`, `_schedule_level`), `schedule_reader.py` (`read()`), `room_controller.py` und bei den Grund-Texten der Übersetzungen. Ein Raum ohne Zeitplan heizt nie vor.
- Offen für das Panel-Ticket 18: Raum-Chips, Raumseite mit Zuweisung, Wochenraster und Zeitleiste, Kopieren, Abtrennen, Löschen, Anlegen eines Helfers, Befehl der Panel API zum Zuweisen samt Tests, „hält Eco“ und „Zeitplan anlegen“ auf der Raumseite, Abnahme per Checkliste.

**Offene Frage (vorgezogener Teil): Aus und Übersteuerung in einem Raum ohne Zeitplan.** Ohne Zeitplan gibt es keinen Schaltpunkt. Heute heißt das: Aus gilt, bis jemand Auto wählt (Grund „Aus“ ohne Zeit), und eine Übersteuerung mit Rückfallregel `next_block` endet nie; mit `earliest` (Standard) und `duration` endet sie nach der Dauer. Dasselbe gilt schon bisher für einen Zeitplan ganz ohne Blöcke. Optionen:
- A: So lassen. Ein Raum ohne Zeitplan ist ein Übergangszustand bis zur Zuweisung im Panel; ein ungenutzter Raum kann bewusst auf Aus bleiben.
- B: Ohne Schaltpunkt enden Aus und Übersteuerung nach der Rückfall-Dauer des Raums (Standard 3 h). Kein Raum bleibt versehentlich tagelang kalt (User Story 9), dafür lässt sich ein ungenutzter Raum ohne Zeitplan nicht dauerhaft ausschalten.
- C: Ohne Schaltpunkt enden Aus und Übersteuerung um Mitternacht.
Empfehlung: B, passend zu „im Zweifel eher warm als kalt“; nicht umgesetzt, bis der Admin entscheidet.

**Teil vorgezogen (Branch `ticket/18-no-schedule`):** Nur die Integrationsteile ohne Panel, nach Freigabe durch den Admin (Handover, Abschnitt „Optional“).
- Umgesetzt: Der Zeitplan ist im Einrichtungs- und Optionsdialog des Raums optional (`CONF_SCHEDULE` ist `Optional`); im Optionsdialog lässt er sich entfernen und nachträglich zuweisen. Ohne Zeitplan, oder wenn der Helfer fehlt oder nicht verfügbar ist, liefert `ScheduleReader.read()` nicht mehr `None`, sondern Eco ohne Schaltpunkt mit `ScheduleLevel.missing`; der Target Resolver entscheidet dann Eco mit dem neuen Grund-Code `no_schedule` („Kein Zeitplan – Eco“ / „No schedule – Eco“). `RoomController._async_evaluate` bricht nicht mehr ab, Fenster offen, Aus, Übersteuerung, Hausbetriebsart und Abwesend wirken weiter. Dialogtexte für Zeitplan und Eco-Temperatur nennen das Verhalten.
- Tests: `tests/test_room_without_schedule.py` (Raum ohne Zeitplan, gelöschter Helfer, Fenster offen, Übersteuerung mit Rückfall nach 3 h, Heizen ohne Temperatur, Zeitplan im Optionsdialog zuweisen und entfernen); `no_schedule` in der Übersetzungsprüfung von `tests/test_reason.py`; der Diagnose-Export zeigt `missing` im Zeitplan-Schnappschuss.
- Hinweis für den Merge mit Ticket 17 (`preheat`): Konflikte erwartet in `target_resolver.py` (`ReasonCode`, `ScheduleLevel`, `_schedule_level`), `schedule_reader.py` (`read()`), `room_controller.py` und bei den Grund-Texten der Übersetzungen. Ein Raum ohne Zeitplan heizt nie vor.
- Offen für das Panel-Ticket 18: Raum-Chips, Raumseite mit Zuweisung, Wochenraster und Zeitleiste, Kopieren, Abtrennen, Löschen, Anlegen eines Helfers, Befehl der Panel API zum Zuweisen samt Tests, „hält Eco“ und „Zeitplan anlegen“ auf der Raumseite, Abnahme per Checkliste.

**Offene Frage (vorgezogener Teil): Aus und Übersteuerung in einem Raum ohne Zeitplan.** Ohne Zeitplan gibt es keinen Schaltpunkt. Heute heißt das: Aus gilt, bis jemand Auto wählt (Grund „Aus“ ohne Zeit), und eine Übersteuerung mit Rückfallregel `next_block` endet nie; mit `earliest` (Standard) und `duration` endet sie nach der Dauer. Dasselbe gilt schon bisher für einen Zeitplan ganz ohne Blöcke. Optionen:
- A: So lassen. Ein Raum ohne Zeitplan ist ein Übergangszustand bis zur Zuweisung im Panel; ein ungenutzter Raum kann bewusst auf Aus bleiben.
- B: Ohne Schaltpunkt enden Aus und Übersteuerung nach der Rückfall-Dauer des Raums (Standard 3 h). Kein Raum bleibt versehentlich tagelang kalt (User Story 9), dafür lässt sich ein ungenutzter Raum ohne Zeitplan nicht dauerhaft ausschalten.
- C: Ohne Schaltpunkt enden Aus und Übersteuerung um Mitternacht.
Empfehlung: B, passend zu „im Zweifel eher warm als kalt“; nicht umgesetzt, bis der Admin entscheidet.

**Entscheidung Admin (25.11.2026):** Option B. In einem Raum ohne Schaltpunkt (kein Zeitplan, fehlender oder nicht verfügbarer Helfer, oder Zeitplan ohne Blöcke) enden Aus und Übersteuerung nach der Rückfall-Dauer des Raums (Standard 3 h), auch bei der Rückfallregel `next_block`. Umgesetzt in `override_expiry_for` (`target_resolver.py`); der Grund zeigt dann z. B. „Aus bis 11:00“. Tests in `tests/test_room_without_schedule.py`: Aus ohne Zeitplan, Übersteuerung mit `next_block` ohne Zeitplan, Aus bei einem Zeitplan ohne Blöcke. Der Rückfallzeitpunkt wird beim Wählen festgelegt; bekommt der Raum danach einen Schaltpunkt, bleibt er bestehen. Spec (Grundsatzentscheidung „Rückfall“) und Glossar („Override expiry“: „`off` always returns at the next block boundary“) nennen diese Ausnahme noch nicht.
