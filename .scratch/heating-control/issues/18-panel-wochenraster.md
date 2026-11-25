# 18: Panel: Wochenraster bearbeiten, Zeitplan anlegen und zuweisen

Spec: `.scratch/heating-control/spec.md`

**What to build:** Im Heating Panel sieht der Admin pro Zeitplan die Woche als Mini-Leiste pro Tag mit Stufenfarben und bearbeitet einen Tag als Zeitleiste (Variante B aus Ticket 16). Er kann Blöcke anlegen, an Griffen verlängern und kürzen, als Ganzes verschieben und löschen und ihnen eine Stufe (Komfort oder Nacht) zuweisen. Jedes Ziehen wird sofort gespeichert. Ein Block lässt sich auf andere Tage kopieren, ein ganzer Tag mit „Tag kopieren nach …“ (Schnellwahl Mo–Fr, Sa–So, Alle). Blöcke über Mitternacht bleiben zwei Blöcke, am Tagesrand steht ein Hinweis auf das Gegenstück. Ein Tipp auf einen Raum in Auto in der Übersicht springt zu seinem Zeitplan mit dem heutigen Tag.

Gilt ein Zeitplan für mehrere Räume, zeigt das Panel „gilt für: …“, einen Hinweis, dass jede Änderung sofort auf alle wirkt, und „Für einen Raum abtrennen“. Gilt er für genau einen Raum, entfällt diese Leiste und der Raumname steht am Zeitplan-Chip. Unter den Zeitplänen erscheinen nur Zeitpläne, die mindestens einem Raum zugewiesen sind.

Für einen Raum kann er direkt einen neuen nativen Zeitplan-Helfer anlegen lassen (Vorlagen „Standardwoche“, „Leer“, „Kopie von …“, Name „Heizung <Raum>“) und ihn dem Raum zuweisen. Ein Zeitplan lässt sich auch mehreren Räumen zuweisen. Verliert ein Zeitplan seinen letzten Raum, bietet das Panel einmal an, ihn zu löschen. Zeitpläne werden ausschließlich über die native Zeitplan-Schnittstelle von Home Assistant gelesen, geschrieben und gelöscht.

Damit ein neuer Raum ohne vorher angelegten Helfer eingerichtet werden kann, wird der Zeitplan im Einrichtungsdialog des Raums optional. Ein Raum ohne Zeitplan, oder dessen Zeitplan-Helfer fehlt oder nicht verfügbar ist, hält Eco mit dem Grund „Kein Zeitplan – Eco“. Alle übrigen Regeln (Fenster offen, Aus, Übersteuerung, Hausbetriebsart, Abwesend) wirken weiter. Das Panel zeigt bei solchen Räumen „Zeitplan anlegen“.

**Blocked by:** 04, 17

**Status:** ready-for-agent

- [ ] Die Wochenübersicht zeigt alle Blöcke eines Zeitplans als Mini-Leiste pro Tag mit Stufenfarben, ein gewählter Tag erscheint als Zeitleiste
- [ ] Blöcke lassen sich auf dem Handy anlegen, an Griffen verlängern und kürzen, verschieben und löschen (15-Minuten-Raster). Jede Änderung wird sofort gespeichert
- [ ] Jedem Block lässt sich eine Stufe zuweisen. Sie wird in den Zusatzdaten des Blocks gespeichert
- [ ] Ein Block lässt sich auf andere Tage kopieren, ein Tag mit „Tag kopieren nach …“ (Mo–Fr, Sa–So, Alle). Ein kopierter Tag ersetzt die Blöcke der Zieltage. Überschneidet ein kopierter Block am Zieltag einen vorhandenen, wird er dort nicht kopiert und das Panel nennt die Tage
- [ ] Blöcke bis 24:00 und ab 00:00 zeigen am Tagesrand einen Hinweis auf das Gegenstück am Nachbartag
- [ ] Ein Tipp auf einen Raum in Auto in der Übersicht öffnet seinen Zeitplan mit dem heutigen Tag
- [ ] Ein neuer Zeitplan-Helfer lässt sich aus dem Panel mit den Vorlagen „Standardwoche“, „Leer“ und „Kopie von …“ anlegen und einem Raum zuweisen
- [ ] Ein Zeitplan lässt sich mehreren Räumen zuweisen. Nur dann zeigt das Panel „gilt für“, den Hinweis und „Für einen Raum abtrennen“
- [ ] Unter den Zeitplänen erscheinen nur zugewiesene Zeitpläne. Verliert ein Zeitplan seinen letzten Raum, fragt das Panel einmal „Löschen / Behalten“
- [ ] Der Zeitplan ist im Einrichtungs- und Optionsdialog des Raums optional. Ohne Zeitplan oder bei fehlendem bzw. nicht verfügbarem Helfer hält der Raum Eco mit Grund-Code `no_schedule`, und alle übrigen Regeln wirken weiter
- [ ] Änderungen wirken sofort auf die betroffenen Räume
- [ ] Mit dem Panel bearbeitete Zeitpläne bleiben im normalen Zeitplan-Editor von Home Assistant bearbeitbar
- [ ] Tests im Test-Home-Assistant decken das Zuweisen über die Panel API und den Raum ohne bzw. mit fehlendem Zeitplan ab, das Wochenraster ist per Checkliste abgenommen

## Comments

**Rückmeldung aus Ticket 16 (25.11.2026):** Fragen 1 bis 7. Hintergrund zum optionalen Zeitplan: Bisher bricht der Room Controller die Auswertung ab, wenn `ScheduleReader.read()` `None` liefert (Helfer fehlt oder ist nicht verfügbar); der Raum behält dann den letzten Sollwert, selbst bei offenem Fenster. Ob die Zeitplan-Bearbeitung im Reiter „Zeitpläne“ oder auf einer Raumseite unter „Räume“ liegt, ist noch offen (Ticket 16, Frage 12).
