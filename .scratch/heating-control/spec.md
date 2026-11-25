# Spec: Smarte, familientaugliche Heizungssteuerung für Home Assistant

Status: ready-for-agent

## Problem Statement

Im Haushalt sind alle Räume mit tado-Heizkörperthermostaten (TRVs) ausgestattet. Diese sind ohne tado-Cloud lokal über HomeKit in Home Assistant eingebunden. Eine Heizungslogik, die Zeitpläne, Fensterkontakte, Anwesenheit und manuelle Eingriffe zusammenführt, gibt es nicht. Die vorhandenen Lösungen sind entweder technisch (Blueprints, Helfer unter Einstellungen) oder bringen eigene, nicht native Konzepte mit.

Aus Sicht der Bewohnerin ist das Problem: Sie bedient die Heizung am Drehknopf oder per Sprache (Siri, später Google). Eine Änderung soll sofort wirken und nicht von einer Automatik überschrieben werden. Trotzdem soll das Haus anschließend wieder von selbst ins richtige Programm zurückfinden. Einen Zeitplan anzupassen darf nicht bedeuten, sich durch Einstellungen → Geräte → Helfer zu suchen.

Aus Sicht des Admins ist das Problem: Alle Zeitpläne sollen an einer Stelle verwaltbar sein und auf nativen Home-Assistant-Bausteinen beruhen. Das System muss nachvollziehbar und robust sein. Die zwei absoluten No-Gos sind „morgens kalt“ und „abends unnötig warm“.

## Solution

Eine Custom Integration erzeugt pro Raum eine eigene `climate`-Entität, das **Raum-Thermostat**. Es ist das einzige Thermostat, das Menschen sehen: in Home Assistant, in Apple Home über die HomeKit-Bridge und später in Google.

Das Raum-Thermostat kennt drei Modi:

- **Auto** folgt dem Zeitplan des Raums.
- **Heizen** bedeutet: Jemand hat manuell übersteuert, und das gilt bis zum Rückfall.
- **Aus** bedeutet Frostschutz bis zum nächsten Schaltpunkt.

Jede Temperaturänderung von außen, etwa am Drehknopf, per Siri oder in der App, wird als manuelle Übersteuerung erkannt und sichtbar als „Heizen“ dargestellt. „Auto“ antippen beendet sie.

Die Zeitpläne sind native `schedule`-Helfer. Jeder Block trägt eine Stufe (Komfort oder Nacht), außerhalb der Blöcke gilt Eco. Die Temperatur jeder Stufe wird pro Raum festgelegt.

Eine eigene Seitenleiste „Heizung“ zeigt alle Räume mit Klartext-Begründung. Dort werden die Wochenpläne bearbeitet und auch angelegt, außerdem Stufentemperaturen, Vorlaufzeiten und die Hausbetriebsart gepflegt.

Fenster offen, Abwesenheit und Urlaub greifen automatisch. Benachrichtigungen gibt es nur für wenige, wichtige Ereignisse und ohne Spam. Bei Ausfällen wird im Zweifel eher warm als kalt geheizt.

## User Stories

### Bedienung im Alltag (Bewohnerin)

1. Als Bewohnerin möchte ich am Drehknopf des Heizkörpers die Temperatur ändern, damit es sofort wärmer oder kälter wird, ohne dass ich eine App brauche.
2. Als Bewohnerin möchte ich, dass meine Änderung am Drehknopf nicht nach kurzer Zeit von der Automatik zurückgedreht wird, damit ich dem System vertraue.
3. Als Bewohnerin möchte ich per Siri „Stell das Wohnzimmer auf 22 Grad“ sagen, damit ich die Heizung freihändig bedienen kann.
4. Als Bewohnerin möchte ich, dass ein Sprachbefehl genauso behandelt wird wie ein Dreh am Knopf, damit ich mir keine Unterschiede merken muss.
5. Als Bewohnerin möchte ich, dass der Raum nach einer manuellen Änderung von selbst wieder ins normale Programm zurückkehrt, damit ich nicht daran denken muss, es zurückzustellen.
6. Als Bewohnerin möchte ich in Apple Home sehen, ob ein Raum auf „Auto“ oder „Heizen“ steht, damit ich erkenne, ob gerade jemand übersteuert hat.
7. Als Bewohnerin möchte ich in Apple Home „Auto“ antippen können, damit der Raum sofort wieder dem Zeitplan folgt.
8. Als Bewohnerin möchte ich einen Raum per Siri oder Apple Home ausschalten können, damit z. B. ein ungenutzter Raum nicht heizt.
9. Als Bewohnerin möchte ich, dass ein ausgeschalteter Raum beim nächsten Schaltpunkt wieder ins Programm zurückkehrt, damit kein Raum versehentlich tagelang kalt bleibt.
10. Als Bewohnerin möchte ich in jedem Raum nur **ein** Thermostat in Apple Home sehen, damit ich nicht das falsche erwische.
11. Als Bewohnerin möchte ich, dass das Bad morgens warm ist, wenn ich aufstehe, damit ich nicht friere.
12. Als Bewohnerin möchte ich, dass abends nicht unnötig weitergeheizt wird, damit es zum Schlafen angenehm kühl ist und keine Energie verschwendet wird.

### Zeitpläne und Stufen (Admin, Bewohnerin mit Admin-Konto)

13. Als Admin möchte ich alle Heizzeitpläne an **einer** Stelle in der Seitenleiste „Heizung“ sehen, damit ich nicht unter Einstellungen → Helfer suchen muss.
14. Als Admin möchte ich den Wochenplan eines Raums in einem Wochenraster mit Blöcken bearbeiten, damit Änderungen schnell und auch auf dem Handy gehen.
15. Als Admin möchte ich jedem Block eine Stufe (Komfort oder Nacht) zuweisen, damit ich nicht in jedem Block eine Temperatur eintippen muss.
16. Als Admin möchte ich, dass außerhalb von Blöcken automatisch Eco gilt, damit ein leerer Zeitraum nie „unbestimmt“ ist.
17. Als Admin möchte ich, dass ein Block ohne Stufenangabe als Komfort gilt, damit von Hand angelegte Blöcke sinnvoll funktionieren.
18. Als Admin möchte ich die Temperaturen von Komfort, Nacht und Eco pro Raum festlegen, damit „Wohnzimmer Komfort 21,5 °C“ an genau einer Stelle steht.
19. Als Admin möchte ich für einen neuen Raum direkt im Panel einen Zeitplan anlegen lassen, damit ich keinen Helfer von Hand erzeugen muss.
20. Als Admin möchte ich einen Zeitplan mehreren Räumen zuweisen können, damit z. B. Wohnzimmer und Küche gemeinsam schalten.
21. Als Admin möchte ich bei einem geteilten Zeitplan sehen, für welche Räume er gilt, damit ich nicht versehentlich andere Räume mitändere.
22. Als Admin möchte ich, dass die Zeitpläne native Home-Assistant-Zeitplan-Helfer sind, damit ich sie auch in eigenen Automationen und anderen Karten nutzen kann.
23. Als Admin möchte ich pro Raum eine Vorlaufzeit festlegen, damit ein Raum zum Blockbeginn bereits warm ist.
24. Als Admin möchte ich, dass eine Änderung am Zeitplan sofort auf die betroffenen Räume wirkt, damit ich das Ergebnis direkt sehe.

### Übersteuerung und Rückfall

25. Als Admin möchte ich global festlegen, wann eine Übersteuerung endet (nächster Schaltpunkt, nach fester Dauer oder beim früheren von beiden), damit das Verhalten zu unserem Alltag passt.
26. Als Admin möchte ich diese Regel pro Raum abweichend einstellen können, damit z. B. das Bad schneller zurückfällt als das Arbeitszimmer.
27. Als Admin möchte ich als Standard „früheres von nächstem Schaltpunkt und 3 Stunden“, damit Übersteuerungen nie ewig hängen bleiben.
28. Als Bewohnerin möchte ich sehen, bis wann meine Übersteuerung gilt, damit ich weiß, was als Nächstes passiert.
29. Als Admin möchte ich, dass eine laufende Übersteuerung einen Neustart von Home Assistant samt Restzeit übersteht, damit ein Update nicht die Wünsche der Familie löscht.
30. Als Admin möchte ich, dass Befehle der Integration an die TRVs **nicht** als Übersteuerung erkannt werden, damit sich das System nicht selbst blockiert.
31. Als Bewohnerin möchte ich, dass bei einem Raum mit mehreren Heizkörpern meine Änderung an einem Knopf für den ganzen Raum gilt, damit alle Heizkörper gleich arbeiten.

### Fenster, Anwesenheit, Urlaub, Hausbetriebsart

32. Als Bewohnerin möchte ich, dass beim Lüften die Heizung im Raum nach kurzer Zeit (60 s) auf Frostschutz geht, damit nicht zum Fenster hinaus geheizt wird.
33. Als Bewohnerin möchte ich, dass nach dem Schließen des Fensters sofort der vorherige Zustand zurückkehrt, eine laufende Übersteuerung eingeschlossen, damit ich nichts neu einstellen muss.
34. Als Admin möchte ich mehrere Fensterkontakte pro Raum angeben, damit jedes offene Fenster zählt.
35. Als Bewohnerin möchte ich, dass beim kurzen Öffnen (unter 60 s) nichts passiert, damit das Lüften nicht jedes Mal die Heizung umschaltet.
36. Als Admin möchte ich, dass das Haus automatisch auf „Abwesend“ absenkt, wenn alle Personen länger als 30 Minuten weg sind, damit leere Räume nicht heizen.
37. Als Bewohnerin möchte ich, dass bei der Rückkehr sofort wieder das normale Programm gilt, damit es schnell warm wird.
38. Als Admin möchte ich „Urlaub“ mit einem Enddatum setzen, damit das Haus während der Reise absenkt und von selbst wieder hochfährt.
39. Als Admin möchte ich die Hausbetriebsart (Automatik, Urlaub, Aus) im Panel und als Entität umschalten können, damit ich sie auch per Siri oder Automation steuern kann.
40. Als Bewohnerin möchte ich, dass meine Übersteuerung auch im Urlaubs- oder Abwesend-Zustand wirkt, damit es warm wird, wenn ich früher nach Hause komme.
41. Als Admin möchte ich die Temperaturen für Abwesend, Urlaub und Frostschutz global festlegen, damit sie für alle Räume einheitlich sind.

### Nachvollziehbarkeit

42. Als Bewohnerin möchte ich für jeden Raum in Klartext sehen, **warum** er gerade so warm oder kalt ist (z. B. „Fenster offen seit 14:03“, „Heizen bis 14:00 (manuell)“, „Komfort bis 22:00“), damit ich das System verstehe.
43. Als Admin möchte ich die Begründung als eigene Sensor-Entität, damit ich sie auf Dashboards und in Automationen nutzen kann.
44. Als Admin möchte ich im Logbuch sehen, wann und warum ein Raum seinen Sollwert geändert hat, damit ich Probleme nachvollziehen kann.
45. Als Admin möchte ich in der Panel-Übersicht pro Raum Ist-Temperatur, Solltemperatur, Modus und Grund sehen, damit ich das ganze Haus auf einen Blick erfasse.
46. Als Admin möchte ich in der Panel-Übersicht eine Übersteuerung mit einem Tipp beenden, damit der Raum zum Zeitplan zurückkehrt.
47. Als Admin möchte ich einen Diagnose-Export der Integration herunterladen, damit ich Fehler melden oder analysieren kann.

### Robustheit und Ausfälle

48. Als Admin möchte ich, dass ein TRV nach einem Verbindungsabbruch automatisch wieder den richtigen Sollwert bekommt, damit ein kurzer Ausfall folgenlos bleibt.
49. Als Admin möchte ich, dass ein TRV, das länger als 30 Minuten nicht erreichbar ist, unter Reparaturen erscheint, damit ich davon erfahre.
50. Als Admin möchte ich, dass ein nicht erreichbarer Fensterkontakt als „geschlossen“ gilt, damit ein leerer Akku nicht dauerhaft die Heizung abschaltet.
51. Als Admin möchte ich, dass eine unbekannte Anwesenheit als „zu Hause“ gilt, damit es im Zweifel nicht kalt wird.
52. Als Admin möchte ich, dass ein Befehl, den das TRV nicht übernommen hat, erkannt und einmal wiederholt wird, damit tado-Eigenheiten den Raum nicht kalt lassen.
53. Als Admin möchte ich, dass die Integration nach einem Neustart von Home Assistant ohne Befehlsflut wieder in den korrekten Zustand findet, damit TRVs und Bridge nicht überlastet werden.

### Benachrichtigungen

54. Als Bewohnerin möchte ich eine Nachricht bekommen, wenn ein Fenster länger als 20 Minuten offen ist, damit ich es nicht vergesse.
55. Als Admin möchte ich eine Nachricht bekommen, wenn ein TRV länger als 30 Minuten offline ist, damit ich reagieren kann.
56. Als Admin möchte ich die Empfänger der Benachrichtigungen auswählen (z. B. die Handys von uns beiden), damit die richtigen Personen informiert werden.
57. Als Bewohnerin möchte ich jedes Ereignis pro Raum nur **einmal** gemeldet bekommen, damit ich nicht zugespammt werde.
58. Als Bewohnerin möchte ich bei mehreren gleichzeitig betroffenen Räumen **eine** gesammelte Nachricht, damit mein Handy nicht mehrfach vibriert.
59. Als Bewohnerin möchte ich zwischen 22 und 7 Uhr keine Nachrichten bekommen, und morgens nur die, die dann noch zutreffen, damit meine Nachtruhe nicht gestört wird.
60. Als Admin möchte ich keine „wieder online“-Nachrichten, damit nur handlungsrelevante Meldungen ankommen.

### Einrichtung

61. Als Admin möchte ich die Integration komplett über die Oberfläche einrichten, ohne YAML, damit sie wartbar bleibt.
62. Als Admin möchte ich pro Raum TRVs, Fensterkontakte und Zeitplan im Einrichtungsdialog auswählen, damit ein neuer Raum in wenigen Minuten steht.
63. Als Admin möchte ich global die Personen für die Anwesenheit, die Benachrichtigungsempfänger und die Ruhezeiten festlegen, damit diese Einstellungen nur einmal existieren.
64. Als Admin möchte ich nachträglich alle Einstellungen über den Optionsdialog ändern, damit ich nichts löschen und neu anlegen muss.
65. Als Admin möchte ich im Einrichtungsdialog einen Hinweis bekommen, nur die Raum-Thermostate und nicht die TRVs an die HomeKit-Bridge zu geben, damit in Apple Home keine doppelten Thermostate auftauchen.
66. Als Admin möchte ich, dass jeder Raum als Gerät erscheint und einem Home-Assistant-Bereich zugeordnet ist, damit er sich in Dashboards und Sprachsteuerung natürlich einfügt.
67. Als Admin möchte ich die Integration als HACS-/Marketplace-kompatibles Repository installieren, damit Updates einfach sind.
68. Als Admin möchte ich die Raum-Thermostate an Google weitergeben können (ohne Nabu Casa), damit Google Home später dieselben Räume steuert.

## Implementation Decisions

### Plattform und Rahmen

- Custom Integration, Mindestversion ist die aktuelle stabile Home-Assistant-Version (2026.11). Die Repository-Struktur ist HACS-/Marketplace-kompatibel.
- Code, Glossar und ADRs sind auf Englisch, die Oberfläche auf Deutsch und Englisch (Übersetzungsdateien). Spezifikation und Tickets sind auf Deutsch.
- Konfiguration ausschließlich über Config Flow und Options Flow. Ein **Haupteintrag** enthält die globalen Einstellungen. Jeder **Raum** ist ein Config-Subentry des Haupteintrags.
- Globale Einstellungen:
  - Personen für die Anwesenheit und Abwesenheitsverzögerung (Standard 30 min)
  - Benachrichtigungsempfänger und Ruhezeit (Standard 22–7 Uhr)
  - Temperaturen für Abwesend, Urlaub und Frostschutz
  - Standard-Rückfallregel (Standard `earliest`, 3 h)
  - Fenster-Verzögerung (Standard 60 s)
- Raum-Einstellungen:
  - ein oder mehrere TRVs
  - null oder mehr Fensterkontakte
  - optional ein Zeitplan-Helfer. Ohne Zeitplan, oder wenn der Helfer fehlt oder nicht verfügbar ist, hält der Raum Eco (Grund „Kein Zeitplan – Eco“), alle übrigen Regeln wirken weiter (Ticket 16)
  - Temperaturen für Komfort, Nacht und Eco
  - Vorlaufzeit
  - optionale abweichende Rückfallregel
  - Bereich (Area)
- Jeder Raum ist ein Gerät in der Geräteverwaltung. Seine Entitäten hängen an diesem Gerät.

### Entitäten

- **Raum-Thermostat** (`climate`) pro Raum:
  - HVAC-Modi: `auto`, `heat`, `off`. Keine Presets, weil Apple Home sie nicht anzeigt.
  - Ist-Temperatur ist der Mittelwert der verfügbaren TRVs.
  - Attribute: Grund, Rückfallzeitpunkt, aktive Stufe.
  - `set_temperature` erzeugt bzw. aktualisiert eine Übersteuerung und setzt den Modus auf `heat`.
  - `set_hvac_mode(auto)` beendet Übersteuerung oder Aus.
  - `set_hvac_mode(off)` gilt bis zum nächsten Schaltpunkt, ohne Schaltpunkt für die Rückfall-Dauer des Raums.
  - `set_hvac_mode(heat)` ohne Temperatur übersteuert mit dem aktuellen Sollwert. Gilt gerade Frostschutz wegen Aus, Fenster offen oder Haus aus, übersteuert er stattdessen mit dem Sollwert, den der Raum ohne diesen Grund hätte (Ticket 07).
- **Grund** (`sensor`) pro Raum: Klartext-Begründung, übersetzt, mit stabilem Grund-Code als Attribut für Automationen. Während der Vorlaufzeit nennt er das Vorheizen („Vorheizen auf Komfort, Beginn 16:30“, Code `preheat`), ohne Zeitplan „Kein Zeitplan – Eco“ (Code `no_schedule`).
- **Hausbetriebsart** (`select`) global: `auto`, `vacation`, `off`.
- **Urlaubsende** (`datetime`) global. Läuft es ab, wechselt die Hausbetriebsart auf `auto`.
- **Abwesend** (`binary_sensor`) global, abgeleitet aus Anwesenheit und Verzögerung.
- **Service `climate_control.start_vacation`** mit Pflichtfeld `end`: setzt Urlaubsende und Hausbetriebsart `vacation` in einem Schritt und lehnt ein Ende ab, das nicht in der Zukunft liegt (Ticket 20).
- Alle eigenen Zustände (Übersteuerung samt Rückfall, Aus samt Rückfall, Hausbetriebsart, Urlaubsende) werden über einen Neustart wiederhergestellt.

### Module

1. **Target Resolver** (tiefes Modul, ohne Home-Assistant-Abhängigkeit)
   - Eingabe ist ein Schnappschuss eines Raums: wirksame Zeitplan-Stufe inklusive Vorlaufzeit, Fenster offen, Raum-Modus mit Übersteuerung und Rückfallzeit, Hausbetriebsart, Abwesend sowie Stufentemperaturen.
   - Ausgabe: Solltemperatur, an die TRVs zu sendender Modus (`heat`/`off`), Grund-Code mit Parametern und der nächste Zeitpunkt, an dem neu bewertet werden muss.
   - Rangfolge, höchste zuerst:
     1. Fenster offen → Frostschutz
     2. Raum-Modus `off` → Frostschutz
     3. Übersteuerung → deren Temperatur
     4. Hausbetriebsart `off` → Frostschutz
     5. Urlaub → Urlaubstemperatur
     6. Abwesend → Abwesend-Temperatur
     7. Zeitplan → Temperatur der Stufe
   - Hausbetriebsart `off` steht unter der Übersteuerung. Eine Übersteuerung schlägt also auch „Haus aus“, Urlaub und Abwesend.
2. **Schedule Reader**
   - Liest den nativen Zeitplan-Helfer: Zustand, Attribute des aktiven Blocks und die Blöcke über die Aktion `schedule.get_schedule`.
   - Die Stufe steht in den Zusatzdaten des Blocks unter einem festen Schlüssel (`level`, Werte `comfort`/`night`). Ein Block ohne Angabe gilt als `comfort`, außerhalb von Blöcken gilt `eco`.
   - Berechnet die wirksame Stufe unter Berücksichtigung der Vorlaufzeit. Beginnt ein Block innerhalb der Vorlaufzeit, gilt bereits seine Stufe, sofern sie im Raum wärmer ist als die bisherige. Vorgeheizt wird also, früher abgesenkt nie (Ticket 04).
   - Berechnet außerdem den nächsten Schaltpunkt.
   - Reagiert auf Änderungen am Helfer, etwa wenn er im Panel bearbeitet wird.
   - Hat der Raum keinen Zeitplan, oder fehlt der Helfer bzw. ist er nicht verfügbar, gilt Eco ohne Schaltpunkt. Die Auswertung des Raums läuft trotzdem weiter.
3. **Room Controller**: einer pro Raum.
   - Abonniert alle Eingaben und hält Übersteuerung und Rückfall.
   - Ruft den Target Resolver auf, plant Neubewertungen zum gelieferten Zeitpunkt und sendet Befehle an die TRVs.
   - Sendet nur bei Abweichung zwischen Soll- und Ist-Zustand des TRV.
   - Bei `heat` gehen Modus und Temperatur immer gemeinsam raus. Ein ausgeschaltetes TRV ignoriert eine Temperatur ohne Modus stillschweigend (Ticket 01).
   - Ein TRV gilt als nicht erreichbar, wenn seine `climate`-Entität **oder** der Temperatursensor desselben Geräts `unavailable` ist. Bei einem Ausfall der Bridge friert die `climate`-Entität nur ein und wird nicht `unavailable` (Ticket 01).
   - Wird ein TRV wieder erreichbar, sendet er den Sollzustand erneut, sobald ein gültiger Modus gemeldet wird. Nach einem Neustart sendet er gedrosselt, also gestaffelt und nicht alle gleichzeitig.
4. **Override Detector**
   - Klassifiziert Zustandsänderungen der TRVs als Echo oder externe Änderung.
   - Gemessen (Ticket 01): Ein eigener Befehl erscheint sofort (< 0,2 s) im Zustand des TRV, mit dem eigenen Kontext, und es gibt keine späteren Echos. Eine Drehung am Knopf kommt erst mit der nächsten Minutenabfrage von Home Assistant an (bis ca. 61 s), nur mit dem Endwert und mit einem neuen Kontext ohne `user_id`/`parent_id`.
   - Regel: Eine Änderung, die vom zuletzt gesendeten Sollzustand abweicht, ist eine externe Änderung. Entprellung und Echo-Fenster sind nicht nötig.
   - Zeigt die erste Abfrage nach einem eigenen Befehl wieder exakt den Zustand vor dem Befehl, gilt der Befehl als nicht übernommen. Dann wird einmal erneut gesendet, und es entsteht keine Übersteuerung.
   - Ausschalten am Gerät wird wie Aus am Raum-Thermostat behandelt.
   - Werte im Modus `off` (`temperature: null`, min/max 7/35) und ein kurzzeitig gemeldeter Modus `None` sind keine Änderungen.
   - Eine externe Änderung an irgendeinem TRV eines Raums wird zur Übersteuerung des ganzen Raums. Die übrigen TRVs werden synchronisiert.
   - Änderungen über die HomeKit-Bridge, Google oder die HA-Oberfläche kommen als Aufruf an das Raum-Thermostat an und brauchen keine Erkennung.
5. **Window and Presence Inputs**
   - Ein Raum gilt als „Fenster offen“, wenn irgendein Kontakt länger als die Fenster-Verzögerung offen ist. Beim Schließen gilt das sofort nicht mehr.
   - Ein nicht erreichbarer Kontakt gilt als geschlossen.
   - Abwesend gilt, wenn alle konfigurierten Personen länger als die Verzögerung nicht `home` sind. Ist eine Anwesenheit unbekannt oder nicht erreichbar, gilt die Person als zu Hause.
6. **Notifier**
   - Zwei Ereignisarten: „Fenster seit 20 min offen“ und „TRV seit 30 min offline“.
   - Jedes Ereignis wird pro Raum nur einmal gemeldet. Neu gemeldet wird erst, wenn der Zustand sich auflöst und erneut eintritt.
   - Gleichzeitige Ereignisse werden zu einer Nachricht gebündelt.
   - Keine Auflösungs-Meldungen („wieder online“).
   - In der Ruhezeit wird zurückgehalten. Danach wird gesammelt gemeldet, was noch zutrifft.
   - Versand über die konfigurierten `notify`-Ziele.
7. **Repairs and Diagnostics**: ein Reparaturhinweis pro TRV, das länger als 30 min nicht erreichbar ist, und ein Diagnose-Export mit Konfiguration, Raum-Schnappschüssen und letzten Entscheidungen.
8. **Logbook**: Jede Änderung des Sollwerts eines Raums erzeugt einen Logbuch-Eintrag mit Grund.
9. **Panel API**: eigene Websocket-Befehle der Integration, nur für Admins.
   - Raumübersicht mit Status lesen und abonnieren.
   - Stufentemperaturen und Vorlaufzeit pro Raum ändern (schreibt in die Subentry-Optionen).
   - Zeitplan einem Raum zuweisen.
   - Hausbetriebsart und Urlaubsende setzen, Urlaub mit Ende in einem Befehl starten.
   - Konfigurierte Personen mit Anwesenheitszustand lesen (für die Abwesend-Anzeige).
   - Übersteuerung eines Raums beenden.
   - Zeitpläne selbst liest, schreibt und löscht das Panel über die nativen Websocket-Befehle des Zeitplan-Helfers (`schedule/list`, `schedule/create`, `schedule/update`, `schedule/delete`). Diese sind nur für Admins erlaubt.
10. **Heating Panel**: eigener Seitenleisten-Eintrag „Heizung“, nur für Admins, für das Handy ausgelegt, von der Integration als JavaScript-Modul ausgeliefert.
    - Inhalte in Version 1:
      - Raumübersicht mit Ist, Soll, Modus und Grund; Antippen beendet die Übersteuerung.
      - Wochenraster des Zeitplans pro Raum mit Blöcken und Stufen, inklusive „gilt für“-Anzeige bei geteilten Zeitplänen.
      - Stufentemperaturen und Vorlaufzeit pro Raum.
      - Hausbetriebsart und Urlaub mit Enddatum.
      - Zeitplan für einen Raum anlegen.
    - Das Panel enthält keine Heizlogik. Es spricht nur mit der Panel API und der nativen Zeitplan-Schnittstelle. Interne `ha-*`-Komponenten des Frontends werden nicht vorausgesetzt.
    - Vor dem Panel entsteht ein klickbarer Wegwerf-Prototyp mit Beispieldaten. Die Rückmeldung des Haushalts verfeinert die Panel-Tickets.
    - Gestaltung laut Abnahme (Ticket 16):
      - Drei Reiter: Übersicht, Räume und Haus. Unter „Räume“ hat jeder Raum eine Seite mit Zuweisung des Zeitplans, Wochenraster, Stufen und Vorlaufzeit. Unter „Haus“ stehen Hausbetriebsart, Urlaub, Abwesend und die globalen Temperaturen. Eine eigene Liste aller Zeitpläne gibt es nicht. Die Heizzeitpläne liegen damit gesammelt unter „Räume“ (User Story 13).
      - Wochenraster als Mini-Leiste pro Tag, bearbeitet wird ein Tag als Zeitleiste mit Ziehgriffen. Blöcke und Tage lassen sich auf andere Tage kopieren.
      - „gilt auch für …“ erscheint nur, wenn der Zeitplan des Raums mehrere Räume hat, zusammen mit „Für <Raum> abtrennen“.
      - Antippen in der Übersicht beendet ohne Nachfrage, mit 6 Sekunden „Rückgängig“. Ein Tipp auf einen Raum in Auto öffnet seine Raumseite.
      - Urlaub wird erst nach Wahl des Endes gestartet.

### Grundsatzentscheidungen

- **Native Zeitplan-Helfer als Datenbasis, Bearbeitung nur durch Admins.** Die Bewohnerin bekommt ein Admin-Konto. Eine Integration kann Zeitplan-Helfer nicht über eine öffentliche Python-API anlegen oder ändern. Deshalb läuft das Anlegen über das Panel mit den Rechten des angemeldeten Admins.
- **tado wird rein lokal über HomeKit betrieben**, ohne tado-App und ohne Cloud. Die TRVs bieten nur `off` und `heat`.
- **Siri läuft über die HomeKit-Bridge von Home Assistant.** Freigegeben werden nur die Raum-Thermostate. Google Home folgt später über die eigene Google-Assistant-Einrichtung ohne Nabu Casa, ebenfalls nur mit den Raum-Thermostaten.
- **Kein eigener Boost.** Die Übersteuerung deckt diesen Anwendungsfall ab.
- **Rückfall:** `heat` endet nach Rückfallregel (`next_block`, `duration` oder `earliest`). `off` endet immer am nächsten Schaltpunkt. Ausnahme: Gibt es keinen Schaltpunkt (kein Zeitplan, fehlender oder nicht verfügbarer Helfer, Zeitplan ohne Blöcke), enden `off` und `heat` nach der Rückfall-Dauer des Raums (Standard 3 h), auch bei `next_block`. Der Rückfallzeitpunkt wird beim Wählen festgelegt (Ticket 18).
- **Mehrere TRVs pro Raum** bekommen immer denselben Sollwert. Als Ist-Temperatur gilt der Mittelwert der verfügbaren TRVs.

## Testing Decisions

- **Eine einzige Test-Schnittstelle**: die Integration in einem echten Test-Home-Assistant über `pytest-homeassistant-custom-component`.
  - Ein Test richtet den Haupteintrag und die Räume ein. Beteiligt sind simulierte TRV-Entitäten (Zustände plus abgefangene `climate`-Aufrufe), echte native Zeitplan-Helfer, Fensterkontakte und Personen.
  - Danach verändert der Test Zustände oder spult die Zeit vor.
  - Er prüft ausschließlich von außen beobachtbares Verhalten: Zustand und Attribute des Raum-Thermostats, Grund-Sensor, gesendete Befehle an die TRVs, Benachrichtigungen, Reparaturhinweise und Antworten der Panel API.
- **Simulierte TRVs bilden das in Ticket 01 gemessene tado-Verhalten nach:**
  - sofortige Übernahme eigener Befehle
  - Drehungen am Knopf erst im Minutentakt der Abfrage, nur mit dem Endwert
  - Ignorieren einer Temperatur ohne Modus im ausgeschalteten Zustand
  - `temperature: null` im Modus `off`
  - Einfrieren statt `unavailable` bei einem Ausfall der Bridge, mit `unavailable` Temperatursensor
  - verzögerte Rückkehr mit kurzzeitig ungültigem Modus
- **Die Rangfolge der Regeln wird über viele kleine Szenarien an dieser Schnittstelle abgedeckt**, nicht über eine zweite Testebene direkt am Target Resolver.
- **Gute Tests** prüfen Verhalten statt Implementierung. Ein Test benennt ein Alltagsszenario mit den Begriffen aus dem Glossar, z. B. „Fenster offen während Übersteuerung stellt Übersteuerung nach Schließen wieder her“. Tests greifen nicht auf interne Zustände des Room Controllers zu.
- **Zeit** wird über die Zeitsteuerung des Test-Frameworks vorgespult, nicht über echte Wartezeiten.
- **Panel**: In Version 1 gibt es keine automatischen Oberflächentests. Die Abnahme erfolgt per Checkliste auf dem Handy. Die Panel API ist über die Test-Schnittstelle abgedeckt.
- **Vorbilder**: Im Repository gibt es noch keine Tests. Vorbild sind die Tests von `generic_thermostat` und `schedule` in Home Assistant Core.

## Out of Scope

- tado-App, tado-Cloud-API, tado-eigene Zeitpläne, Geofencing und Fenstererkennung von tado
- Ansteuerung von Kessel oder Wärmepumpe. Ein Wärmebedarf-Signal kommt in Version 2.
- Lernendes Vorheizen (Version 2). In Version 1 gilt eine feste Vorlaufzeit.
- Feiertage über `workday` (Version 2)
- Externe Raumtemperatursensoren und Offset-Kalibrierung
- Schaltaktoren (`switch`) als Aktoren
- Fenstererkennung über einen Temperatursturz
- Bearbeitung von Zeitplänen durch Nicht-Admins
- Batterie-Benachrichtigungen: tado liefert über HomeKit keinen Batteriestand (Ticket 01)
- Nabu Casa und eine spezielle Google-Home-Anpassung über das reine Durchreichen hinaus
- Automatisierte Oberflächentests des Panels
- Eine eigene Dashboard-Karte neben dem Panel

## Further Notes

- **Das Messprotokoll an der echten Hardware (Ticket 01) ist abgeschlossen.** Ergebnisse:
  - TRVs bieten `off`/`heat` mit 5–25 °C und Luftfeuchte, aber keinen Batteriestand.
  - Home Assistant fragt sie nur im Minutentakt ab und erhält keine Push-Meldungen.
  - Eigene Befehle erzeugen keine Echos.
  - Bei einem Ausfall der Bridge friert die `climate`-Entität ein, statt `unavailable` zu werden.
  
  Die Folgerungen stehen in den Modulen Room Controller und Override Detector sowie in den Tickets 08 und 13.
- **Schrittweite: 1 °C** (entschieden in Ticket 16), passend zum Knopf, der in 1-°C-Schritten arbeitet. Sie gilt im Panel, im Einrichtungs- und Optionsdialog und am Raum-Thermostat. Ob die TRVs per Befehl halbe Grad annehmen, spielt damit keine Rolle mehr.
- **Das Panel wird nach dem ersten Sichten durch den Haushalt nachgeschärft.** Der Prototyp ist dafür ein eigener Abstimmungsschritt.
- **Offen: Anzahl der Räume.** Sie ist nicht blockierend und dient nur der Abschätzung. Mehrere TRVs pro Raum werden unterstützt.
- Die Test-Schnittstelle wird nach den ersten Tickets mit dem Admin noch einmal angeschaut.
- Fachbegriffe stehen in `GLOSSARY.md` und sind verbindlich für Ticket-Titel, Code und Testnamen.
