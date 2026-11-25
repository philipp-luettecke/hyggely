// Rooms tab: room chips, then the page of the chosen room. The page shows the
// room's target and reason, then the section of ticket 18 (schedule) and the
// section of ticket 19 (levels and lead time), each in its own file.

import { LitElement, css, html, type PropertyDeclarations } from "lit";
import type { RoomOverview } from "../api/rooms";
import { formatTemperature, localize } from "../i18n";
import { navigate } from "../navigation";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import "./levels-section";
import "./schedule-section";
import { defineOnce } from "../define";

const TEXTS = {
  de: {
    targetNow: "Soll jetzt",
    noRooms: "Noch keine Räume. Lege sie in den Einstellungen der Integration an.",
  },
  en: {
    targetNow: "Target now",
    noRooms: "No rooms yet. Add them in the settings of the integration.",
  },
};

export class RoomsTab extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    rooms: { attribute: false },
    roomId: { attribute: false },
  };

  hass?: HomeAssistant;
  rooms: RoomOverview[] = [];
  roomId?: string;

  protected override render() {
    const t = localize(this.hass, TEXTS);
    const room = this.rooms.find((candidate) => candidate.room_id === this.roomId) ?? this.rooms[0];
    if (!room) {
      return html`<p class="muted">${t.noRooms}</p>`;
    }
    return html`
      <div class="chips" role="tablist">
        ${this.rooms.map(
          (candidate) => html`<button
            class="chip ${candidate === room ? "selected" : ""}"
            role="tab"
            aria-selected=${candidate === room}
            @click=${() => navigate(this, "rooms", candidate.room_id)}
          >
            ${candidate.name}
          </button>`,
        )}
      </div>
      <div class="card pad">
        <div class="name">${room.name}</div>
        <div class="muted small">
          ${t.targetNow} ${formatTemperature(this.hass, room.target_temperature)} · ${room.reason ?? ""}
        </div>
      </div>
      <cc-room-schedule-section .hass=${this.hass} .room=${room}></cc-room-schedule-section>
      <cc-room-levels-section .hass=${this.hass} .room=${room}></cc-room-levels-section>
    `;
  }

  static override styles = [
    sharedStyles,
    css`
      .name {
        font-weight: 600;
        margin-bottom: 2px;
      }
    `,
  ];
}

defineOnce("cc-rooms-tab", RoomsTab);
