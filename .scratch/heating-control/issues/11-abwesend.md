# 11: Abwesend

Spec: `.scratch/heating-control/spec.md`

**What to build:** Sind alle im Haupteintrag konfigurierten Personen länger als die Abwesend-Verzögerung (Standard 30 min) nicht zu Hause, gilt Abwesend. Alle Räume im Modus Auto erhalten dann die Abwesend-Temperatur. Kommt jemand zurück, gilt sofort wieder die Zeitplan-Stufe. Eine unbekannte oder nicht erreichbare Anwesenheit gilt als „zu Hause“. Es gibt eine globale Entität „Abwesend“, und der Grund-Sensor zeigt „Abwesend“.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Eine globale Entität zeigt, ob Abwesend gilt
- [ ] Abwesend gilt erst, wenn alle Personen länger als die Verzögerung weg sind
- [ ] Kehrt eine Person zurück, endet Abwesend sofort
- [ ] Eine Person mit unbekanntem oder nicht erreichbarem Zustand gilt als zu Hause
- [ ] Räume im Modus Auto erhalten bei Abwesend die globale Abwesend-Temperatur
- [ ] Der Grund-Sensor zeigt Abwesend
- [ ] Szenario-Tests decken Verzögerung, Rückkehr, unbekannte Anwesenheit und mehrere Personen ab
