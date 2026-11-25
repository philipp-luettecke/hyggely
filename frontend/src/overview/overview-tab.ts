// Overview tab: every room with current temperature, target, room mode and
// reason. A tap on a room in heat or off returns it to auto, without asking:
// the command goes out after the undo time, or at once when the panel is left.

import { LitElement, css, html, nothing, type PropertyDeclarations } from "lit";
import { returnToAuto, type RoomMode, type RoomOverview } from "../api/rooms";
import "../house/house-status";
import { errorMessage, format, formatTemperature, localize } from "../i18n";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";

export const UNDO_SECONDS = 6;

const TEXTS = {
  de: {
    auto: "Auto",
    heat: "Heizen",
    off: "Aus",
    target: "Soll",
    endOverride: "Antippen beendet die Übersteuerung → Auto",
    endOff: "Antippen beendet „Aus“ → Auto",
    pending: "Kehrt zu Auto zurück …",
    returning: "{room} kehrt zu Auto zurück",
    undo: "Rückgängig",
    dismiss: "OK",
    failed: "{room} konnte nicht auf Auto gestellt werden: {error}",
    noRooms: "Noch keine Räume. Lege sie in den Einstellungen der Integration an.",
  },
  en: {
    auto: "Auto",
    heat: "Heat",
    off: "Off",
    target: "Target",
    endOverride: "Tap to end the override → Auto",
    endOff: "Tap to end “Off” → Auto",
    pending: "Returning to auto …",
    returning: "{room} returns to auto",
    undo: "Undo",
    dismiss: "OK",
    failed: "{room} could not be set to auto: {error}",
    noRooms: "No rooms yet. Add them in the settings of the integration.",
  },
};

type Text = (typeof TEXTS)["de"];

const REASON_COLOURS: Record<string, string> = {
  override: "heat",
  window_open: "frost",
  room_off: "off",
  house_off: "off",
  vacation: "night",
  away: "night",
};

interface PendingReturn {
  roomId: string;
  name: string;
  timer: number;
}

export class OverviewTab extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    rooms: { attribute: false },
    _pending: { state: true },
    _error: { state: true },
  };

  hass?: HomeAssistant;
  rooms: RoomOverview[] = [];
  private _pending?: PendingReturn;
  private _error?: string;

  override connectedCallback(): void {
    super.connectedCallback();
    document.addEventListener("visibilitychange", this._sendWhenHidden);
    window.addEventListener("pagehide", this._sendPending);
  }

  override disconnectedCallback(): void {
    document.removeEventListener("visibilitychange", this._sendWhenHidden);
    window.removeEventListener("pagehide", this._sendPending);
    this._sendPending();
    super.disconnectedCallback();
  }

  protected override render() {
    const t = localize(this.hass, TEXTS);
    return html`
      <cc-house-status .hass=${this.hass}></cc-house-status>
      ${this.rooms.length === 0 ? html`<p class="muted">${t.noRooms}</p>` : nothing}
      <div class="grid">${this.rooms.map((room) => this._card(room, t))}</div>
      ${this._toast(t)}
    `;
  }

  private _card(room: RoomOverview, t: Text) {
    const pending = this._pending?.roomId === room.room_id;
    const mode: RoomMode = pending ? "auto" : room.room_mode;
    const colour = REASON_COLOURS[room.reason_code ?? ""] ?? "auto";
    let foot: string | typeof nothing = nothing;
    if (pending) {
      foot = t.pending;
    } else if (room.room_mode === "heat") {
      foot = t.endOverride;
    } else if (room.room_mode === "off") {
      foot = t.endOff;
    }
    return html`
      <div
        class="card room colour-${colour} ${pending ? "pending" : ""}"
        role="button"
        tabindex="0"
        @click=${() => this._tap(room)}
        @keydown=${(event: KeyboardEvent) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            this._tap(room);
          }
        }}
      >
        <div class="top">
          <span class="name">${room.name}</span>
          <span class="mode mode-${mode}">${t[mode]}</span>
        </div>
        <div class="temps">
          <span class="current">${formatTemperature(this.hass, room.current_temperature)}</span>
          <span class="target">
            <span class="muted">${t.target}</span>
            ${formatTemperature(this.hass, room.target_temperature)}
          </span>
        </div>
        <div class="reason">${room.reason ?? ""}</div>
        <div class="foot ${pending ? "muted" : ""}">${foot}</div>
      </div>
    `;
  }

  private _toast(t: Text) {
    if (this._pending) {
      return html`<div class="toast" role="status">
        <span>${format(t.returning, { room: this._pending.name })}</span>
        <button @click=${this._undo}>${t.undo}</button>
      </div>`;
    }
    if (this._error) {
      return html`<div class="toast" role="alert">
        <span>${this._error}</span>
        <button @click=${() => (this._error = undefined)}>${t.dismiss}</button>
      </div>`;
    }
    return nothing;
  }

  private _tap(room: RoomOverview): void {
    // A room in auto opens its room page (ticket 18).
    if (room.room_mode === "auto" || this._pending?.roomId === room.room_id) {
      return;
    }
    this._sendPending();
    this._error = undefined;
    this._pending = {
      roomId: room.room_id,
      name: room.name,
      timer: window.setTimeout(this._sendPending, UNDO_SECONDS * 1000),
    };
  }

  private _undo = (): void => {
    if (this._pending) {
      window.clearTimeout(this._pending.timer);
      this._pending = undefined;
    }
  };

  private _sendWhenHidden = (): void => {
    if (document.visibilityState === "hidden") {
      this._sendPending();
    }
  };

  private _sendPending = (): void => {
    const pending = this._pending;
    if (!pending || !this.hass) {
      return;
    }
    window.clearTimeout(pending.timer);
    this._pending = undefined;
    returnToAuto(this.hass, pending.roomId).catch((error: unknown) => {
      const t = localize(this.hass, TEXTS);
      this._error = format(t.failed, { room: pending.name, error: errorMessage(error) });
    });
  };

  static override styles = [
    sharedStyles,
    css`
      .grid {
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
      }
      .grid > .card {
        margin: 0;
      }
      .room {
        padding: 14px;
        border-left: 5px solid var(--cc-auto);
        cursor: pointer;
        user-select: none;
        -webkit-user-select: none;
      }
      .room:active {
        filter: brightness(0.96);
      }
      .room:focus-visible {
        outline: 2px solid var(--cc-primary);
      }
      .colour-heat {
        border-left-color: var(--cc-heat);
      }
      .colour-frost {
        border-left-color: var(--cc-frost);
      }
      .colour-off {
        border-left-color: var(--cc-off);
      }
      .colour-night {
        border-left-color: var(--cc-night);
      }
      .pending {
        opacity: 0.7;
      }
      .top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
      }
      .name {
        font-size: 17px;
        font-weight: 500;
      }
      .mode {
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 13px;
        font-weight: 500;
        color: #fff;
      }
      .mode-auto {
        background: var(--cc-auto);
      }
      .mode-heat {
        background: var(--cc-heat);
      }
      .mode-off {
        background: var(--cc-off);
      }
      .temps {
        display: flex;
        align-items: baseline;
        gap: 14px;
        margin: 6px 0 2px;
      }
      .current {
        font-size: 30px;
      }
      .target {
        font-size: 16px;
      }
      .reason {
        font-size: 15px;
      }
      .foot {
        margin-top: 8px;
        min-height: 20px;
        font-size: 13px;
        font-weight: 500;
        color: var(--cc-heat);
      }
      .foot.muted {
        color: var(--cc-muted);
        font-weight: normal;
      }
      .toast {
        position: fixed;
        left: 50%;
        transform: translateX(-50%);
        bottom: calc(16px + env(safe-area-inset-bottom));
        z-index: 10;
        display: flex;
        gap: 14px;
        align-items: center;
        width: max-content;
        max-width: calc(100vw - 32px);
        padding: 10px 14px;
        background: #323232;
        color: #fff;
        border-radius: 8px;
        font-size: 14px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
      }
      .toast button {
        border: 0;
        background: transparent;
        color: #81d4fa;
        font: inherit;
        font-weight: 600;
        padding: 6px 4px;
        cursor: pointer;
      }
    `,
  ];
}

defineOnce("cc-overview-tab", OverviewTab);
