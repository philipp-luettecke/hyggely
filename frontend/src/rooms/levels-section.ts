// Room page, section of ticket 19: temperatures of comfort, night and eco and
// the lead time of the room.

import { LitElement, type PropertyDeclarations } from "lit";
import type { RoomOverview } from "../api/rooms";
import { localize } from "../i18n";
import { placeholderSection } from "../placeholder";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";

const TEXTS = {
  de: { title: "Stufen und Vorlaufzeit" },
  en: { title: "Levels and lead time" },
};

export class RoomLevelsSection extends LitElement {
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

defineOnce("cc-room-levels-section", RoomLevelsSection);
