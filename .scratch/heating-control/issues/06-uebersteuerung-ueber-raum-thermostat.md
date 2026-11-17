# 06 – Übersteuerung über das Raum-Thermostat

Status: ready-for-agent
Blocked by: 03
Spec: `.scratch/heating-control/spec.md`

## What to build

Ändert jemand die Temperatur am **Raum-Thermostat**, entsteht eine **Übersteuerung**. Das gilt per Siri über die HomeKit-Bridge, in der HA-App oder über ein Dashboard.

- Der Raum wechselt sichtbar auf `heat`, und das TRV bekommt die gewünschte Temperatur.
- `set_hvac_mode(heat)` ohne Temperatur übersteuert mit dem aktuellen Sollwert.
- `set_hvac_mode(auto)` beendet die Übersteuerung sofort.

Die Übersteuerung endet automatisch (**Rückfall**) nach der Regel des Raums:

- `next_block`: am nächsten Schaltpunkt
- `duration`: nach fester Dauer
- `earliest`: beim früheren von beiden

Standard ist die globale Regel (`earliest`, 3 h). Sie kann pro Raum in den Subentry-Optionen abweichend eingestellt werden.

Das Raum-Thermostat zeigt den Rückfallzeitpunkt als Attribut, der Grund-Sensor etwa „Heizen bis 14:00 (manuell)“.

Übersteuerung und Rückfallzeitpunkt überstehen einen Neustart von Home Assistant. Ist der Rückfall während des Neustarts abgelaufen, gilt nach dem Start sofort wieder `auto`.

## Acceptance criteria

- [ ] `set_temperature` im Modus `auto` → Modus `heat`, TRV bekommt `heat` + Temperatur, Grund zeigt Übersteuerung mit Ende
- [ ] Erneutes `set_temperature` während Übersteuerung aktualisiert die Temperatur; der Rückfallzeitpunkt richtet sich nach der Regel neu aus
- [ ] `auto` beendet die Übersteuerung sofort und stellt die Zeitplan-Stufe her
- [ ] Alle drei Rückfallregeln verhalten sich wie beschrieben, global und pro Raum abweichend
- [ ] Neustart mit laufender Übersteuerung: danach weiterhin `heat` mit gleicher Restzeit; abgelaufene Übersteuerung → `auto`
- [ ] Szenario-Tests decken alle Kriterien ab, inklusive Neustart

## Blocked by

- 03 – Ein Raum folgt dem Zeitplan
