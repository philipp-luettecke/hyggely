// Room page, section of ticket 18: assignment of the schedule, "applies also
// to", legend, week overview and day timeline (variant B).

import { LitElement, type PropertyDeclarations } from "lit";
import type { RoomOverview } from "../api/rooms";
import { localize } from "../i18n";
import { placeholderSection } from "../placeholder";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";

const TEXTS = {
  de: { title: "Zeitplan" },
  en: { title: "Schedule" },
};

export class RoomScheduleSection extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    room: { attribute: false },
  };

  static override styles = sharedStyles;

  hass?: HomeAssistant;
  room?: RoomOverview;

  protected override render() {
    return placeholderSection(this.hass, localize(this.hass, TEXTS).title);
  }
}

defineOnce("cc-room-schedule-section", RoomScheduleSection);
