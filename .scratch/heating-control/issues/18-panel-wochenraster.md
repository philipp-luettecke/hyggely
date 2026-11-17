# 18: Panel: Wochenraster bearbeiten, Zeitplan anlegen und zuweisen

Spec: `.scratch/heating-control/spec.md`

**What to build:** Im Heating Panel sieht der Admin pro Zeitplan ein Wochenraster mit Blöcken und Stufen sowie „gilt für: …“. Er kann Blöcke anlegen, verschieben, in der Länge ändern und löschen und ihnen eine Stufe (Komfort oder Nacht) zuweisen. Für einen Raum ohne passenden Zeitplan kann er direkt einen neuen nativen Zeitplan-Helfer anlegen lassen und ihn dem Raum zuweisen. Ein Zeitplan lässt sich auch mehreren Räumen zuweisen. Zeitpläne werden ausschließlich über die native Zeitplan-Schnittstelle von Home Assistant gelesen und geschrieben. Bedienung laut der in Ticket 16 gewählten Variante.

**Blocked by:** 04, 17

**Status:** ready-for-agent

- [ ] Das Wochenraster zeigt alle Blöcke eines Zeitplans mit Stufe und die zugeordneten Räume
- [ ] Blöcke lassen sich auf dem Handy anlegen, verschieben, verlängern, kürzen und löschen
- [ ] Jedem Block lässt sich eine Stufe zuweisen. Sie wird in den Zusatzdaten des Blocks gespeichert
- [ ] Ein neuer Zeitplan-Helfer lässt sich aus dem Panel anlegen und einem Raum zuweisen
- [ ] Ein Zeitplan lässt sich mehreren Räumen zuweisen, und das Panel zeigt die Zuordnung
- [ ] Änderungen wirken sofort auf die betroffenen Räume
- [ ] Mit dem Panel bearbeitete Zeitpläne bleiben im normalen Zeitplan-Editor von Home Assistant bearbeitbar
- [ ] Tests im Test-Home-Assistant decken das Zuweisen über die Panel API ab, das Wochenraster ist per Checkliste abgenommen
