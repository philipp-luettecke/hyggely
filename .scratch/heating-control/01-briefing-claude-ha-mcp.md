# Briefing: Messprotokoll tado-Heizkörperthermostat über HomeKit

Du hast Zugriff auf meine Home-Assistant-Instanz über MCP. Hilf mir, ein Messprotokoll zu erstellen, das beschreibt, wie sich meine tado-Heizkörperthermostate in Home Assistant verhalten. Die Ergebnisse dienen als Grundlage für eine selbst entwickelte Heizungssteuerung. Diese muss unterscheiden können, ob eine Temperaturänderung am Thermostat von ihr selbst stammt oder von einem Menschen am Drehknopf.

## Hintergrund

- Die Thermostate sind tado V3+. Sie sind **ohne tado-Cloud** über die Integration **HomeKit Device** (`homekit_controller`) lokal eingebunden und erscheinen als `climate.*`-Entitäten.
- Die tado-Bridge hat keinen Internetzugang. Die tado-App spielt keine Rolle.
- Ich (der Mensch) kann am Thermostat drehen und die Bridge vom Strom trennen. Du kannst über MCP Zustände lesen, Aktionen ausführen und, falls verfügbar, die Historie oder das Logbuch abfragen.

## Regeln

1. Arbeite nur mit **einem** Thermostat, das ich dir nenne. Ändere keine anderen Geräte.
2. Notiere **vor** der ersten Änderung den Ausgangszustand (Modus und Solltemperatur) und stelle ihn **am Ende** wieder her.
3. Führe Aktionen erst aus, wenn ich „los“ sage, und kündige jede Aktion vorher in einem Satz an.
4. Rate keine Werte. Kannst du etwas über deine Werkzeuge nicht ermitteln, schreibe „nicht ermittelbar über MCP“ und sag mir, was ich stattdessen in der Oberfläche nachsehen soll.
5. Zeitangaben immer mit Sekunden und Zeitzone, z. B. `10:42:17 CET`.

## Schritt 0: Werkzeuge prüfen

Prüfe zuerst, welche deiner MCP-Werkzeuge Folgendes können, und berichte mir das kurz:

- Alle Attribute einer Entität lesen
- `last_changed` und `last_updated` einer Entität lesen
- Eine beliebige Aktion aufrufen, z. B. `climate.set_temperature` mit `hvac_mode`, oder nur vereinfachte Sprachaktionen
- Die Historie einer Entität für einen Zeitraum abrufen, mit allen Zwischenzuständen und Zeitstempeln
- Das Logbuch abrufen, insbesondere mit `context_id` und `context_user_id`
- Geräte und Entitäten eines Geräts auflisten

Frag mich danach nach der Entity-ID des Thermostats, falls ich sie nicht genannt habe. Schlag mir sonst Kandidaten vor, also `climate.*`-Entitäten der Integration HomeKit Device.

## Messung A: Eigenschaften der Entität (machst du allein)

- Lies alle Attribute des Thermostats. Wichtig sind `hvac_modes`, `min_temp`, `max_temp`, `target_temp_step`, `temperature`, `current_temperature`, `current_humidity`, `hvac_action` und `supported_features`.
- Liste alle Entitäten desselben Geräts auf. Gibt es eine Entität zur Batterie (`sensor.*battery*` oder `binary_sensor.*battery*`)? Wenn ja, mit welchem Wert?

## Messung B: Zeit von einer Drehung am Knopf bis zur Zustandsänderung in Home Assistant (wir beide, 5 Durchgänge)

Ablauf je Durchgang:

1. Du liest den aktuellen Zustand und meldest „bereit, Solltemperatur ist X“.
2. Ich drehe um **einen** Schritt und sage dir die **Uhrzeit mit Sekunden**, zu der ich gedreht habe. Ich lese sie von einer Uhr mit Sekundenanzeige ab.
3. Du fragst den Zustand alle paar Sekunden ab oder liest danach die Historie. Ermittle den Zeitstempel (`last_updated`), zu dem die neue Solltemperatur in Home Assistant angekommen ist.
4. Berechne die Differenz in Sekunden.
5. Zwischen den Durchgängen 1 Minute Pause.

Danach ein Sonderdurchgang: Ich drehe **schnell mehrere Schritte** hintereinander (z. B. 4 Schritte in 3 s). Ermittle aus der Historie, wie viele Zustandsänderungen ankamen und mit welchen Werten: jeder Zwischenschritt oder nur der Endwert?

Falls du die `context`-Werte (`id`, `parent_id`, `user_id`) einer dieser Änderungen sehen kannst, zum Beispiel über das Logbuch, notiere sie.

## Messung C: Echo nach einem Befehl (machst du allein)

1. Rufe `climate.set_temperature` auf: Ziel ist das Thermostat, `temperature` ist der aktuelle Wert plus 1 °C, dazu `hvac_mode: heat`. Notiere die Uhrzeit des Aufrufs.
2. Lies in den nächsten 30 s mehrfach den Zustand oder danach die Historie. Notiere **jede** Zustandsänderung mit Zeitpunkt relativ zum Aufruf, Solltemperatur und Zustand (`heat`/`off`).
3. Gibt es Zwischenwerte, z. B. erst den alten Wert, dann den neuen, oder springt der Wert hin und her?
4. Wiederhole das einmal.

## Messung D: Temperatur setzen, während das Thermostat auf „Aus“ steht (machst du allein)

1. `climate.set_hvac_mode` mit `off`. 30 s warten.
2. `climate.set_temperature` nur mit `temperature`, **ohne** `hvac_mode`.
3. 30 s beobachten: Wechselt der Zustand auf `heat`? Springt er nach einigen Sekunden von selbst zurück auf `off`? Wann genau?
4. Wiederhole das Ganze, diesmal mit `hvac_mode: heat` im selben Aufruf von `set_temperature`.

Falls dein Werkzeug `set_temperature` nicht mit `hvac_mode` aufrufen kann, sag mir das. Dann mache ich diesen Teil über **Entwicklerwerkzeuge → Aktionen**.

## Messung E: Bridge stromlos (wir beide)

1. Du notierst den Zustand und sagst „bereit“.
2. Ich ziehe den Stecker der Bridge, nenne dir die Uhrzeit, warte 60 s, stecke wieder ein und nenne dir wieder die Uhrzeit.
3. Ermittle aus der Historie, wann das Thermostat `unavailable` wurde und wann es wieder verfügbar war. Wie lauten danach Modus und Solltemperatur? Gab es Zwischenzustände (z. B. `unknown`)?
4. Ist es nach 5 min immer noch nicht verfügbar, sag mir Bescheid. Dann prüfe ich, ob ich die Integration neu laden muss.

## Abschluss

1. Stelle den Ausgangszustand aus den Regeln wieder her und bestätige ihn mit einem erneuten Lesen.
2. Gib mir das Ergebnis **exakt in der Vorlage unten** als Markdown aus, damit ich es in mein Ticket kopieren kann.
3. Schreibe darunter eine Kurzfassung mit diesen sechs Werten. Sie brauche ich für die Entwicklung:
   - die längste gemessene Verzögerung von einer Drehung am Knopf bis zu Home Assistant
   - ob beim schnellen Drehen Zwischenwerte ankommen
   - Anzahl und Zeitfenster der Echos nach einem eigenen Befehl
   - ob das Thermostat nach einem Temperaturbefehl auf „Aus“ zurückspringt, und ob `hvac_mode: heat` im selben Aufruf das verhindert
   - ob ein Batteriestand verfügbar ist
   - wie lange es nach dem Wiedereinstecken der Bridge dauert, bis das Thermostat wieder verfügbar ist

## Ergebnisvorlage

```markdown
## Ergebnis A

Entity-ID:
Attribute: (Liste)
Batterie verfügbar: ja/nein (Entität, Wert)

## Ergebnis B

| Durchgang | Gedreht um | In HA angekommen (last_updated) | Sekunden | Bemerkung |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| Schnelles Drehen | | | | Anzahl Änderungen: …, Werte: … |

Context einer Drehung am Knopf (falls ermittelbar): id … / parent_id … / user_id …

## Ergebnis C

| Durchgang | Zeit ab Aufruf (s) | Solltemperatur | Zustand | Bemerkung |
|---|---|---|---|---|

## Ergebnis D

Ohne hvac_mode: (Ablauf mit Zeiten)
Mit hvac_mode heat: (Ablauf mit Zeiten)

## Ergebnis E

Stecker gezogen: … / unavailable ab: … / wieder eingesteckt: … / verfügbar ab: …
Zustand danach: …
Neu laden nötig: ja/nein

## Kurzfassung

(die sechs Werte)
```
