// Room page, section of ticket 19: temperatures of comfort, night and eco and
// the lead time of the room.

import { LitElement, css, html, nothing, type PropertyDeclarations, type PropertyValues } from "lit";
import { getRoomLevels, setRoomLevels, type RoomLevels } from "../api/levels";
import type { RoomOverview } from "../api/rooms";
import { errorMessage, format, formatTemperature, localize } from "../i18n";
import {
  DelayedSave,
  MAX_LEAD_TIME_MINUTES,
  MAX_TEMPERATURE,
  MIN_TEMPERATURE,
  stepLeadTime,
  stepper,
  stepperStyles,
  stepTemperature,
} from "../stepper";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";

const TEXTS = {
  de: {
    title: "Stufen und Vorlaufzeit",
    comfort: "Komfort",
    night: "Nacht",
    eco: "Eco",
    leadTime: "Vorlaufzeit",
    leadTimeNote: "So lange vor Beginn eines Blocks gilt bereits seine Stufe, wenn sie wärmer ist.",
    warmer: "{level} ist wärmer als Komfort – gewollt?",
    less: "{name} weniger",
    more: "{name} mehr",
    loading: "Lade Stufen …",
    failed: "Konnte nicht gespeichert werden: {error}",
    loadFailed: "Stufen konnten nicht geladen werden: {error}",
  },
  en: {
    title: "Levels and lead time",
    comfort: "Comfort",
    night: "Night",
    eco: "Eco",
    leadTime: "Lead time",
    leadTimeNote: "A warmer level of a block already applies this long before the block starts.",
    warmer: "{level} is warmer than comfort – intended?",
    less: "{name} lower",
    more: "{name} higher",
    loading: "Loading levels …",
    failed: "Could not be saved: {error}",
    loadFailed: "Levels could not be loaded: {error}",
  },
};

type Text = (typeof TEXTS)["de"];
type Level = "comfort" | "night" | "eco";
type TemperatureKey = `${Level}_temperature`;

const LEVELS: Level[] = ["comfort", "night", "eco"];

/** A lead time as people read it, e.g. `45 min` or `1 h 30 min`. */
export function formatLeadTime(minutes: number): string {
  const total = Math.round(minutes);
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  if (hours === 0) {
    return `${rest} min`;
  }
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
}

export class RoomLevelsSection extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    room: { attribute: false },
    _levels: { state: true },
    _error: { state: true },
  };

  hass?: HomeAssistant;
  room?: RoomOverview;
  private _levels?: RoomLevels;
  private _error?: string;
  private _loadedRoomId?: string;
  private _save?: DelayedSave<RoomLevels>;

  override connectedCallback(): void {
    super.connectedCallback();
    this._save?.connect();
  }

  override disconnectedCallback(): void {
    this._save?.disconnect();
    super.disconnectedCallback();
  }

  protected override willUpdate(changed: PropertyValues): void {
    if ((changed.has("room") || changed.has("hass")) && this.room?.room_id !== this._loadedRoomId) {
      this._load();
    }
  }

  private _load(): void {
    const hass = this.hass;
    const roomId = this.room?.room_id;
    if (!hass || !roomId) {
      return;
    }
    this._save?.disconnect();
    this._loadedRoomId = roomId;
    this._levels = undefined;
    this._error = undefined;
    this._save = new DelayedSave<RoomLevels>((changes) => this._send(hass, roomId, changes));
    this._save.connect();
    getRoomLevels(hass, roomId)
      .then((levels) => {
        if (this._loadedRoomId === roomId) {
          this._levels = levels;
        }
      })
      .catch((error: unknown) => {
        if (this._loadedRoomId === roomId) {
          this._error = format(localize(this.hass, TEXTS).loadFailed, { error: errorMessage(error) });
        }
      });
  }

  private _send(hass: HomeAssistant, roomId: string, changes: Partial<RoomLevels>): void {
    if (this._loadedRoomId === roomId && this._levels) {
      this._levels = { ...this._levels, ...changes };
    }
    setRoomLevels(hass, roomId, changes).catch((error: unknown) => {
      if (this._loadedRoomId === roomId) {
        this._loadedRoomId = undefined;
        this._load();
        this._error = format(localize(this.hass, TEXTS).failed, { error: errorMessage(error) });
      }
    });
  }

  protected override render() {
    const t = localize(this.hass, TEXTS);
    return html`<h2 class="section">${t.title}</h2>
      <div class="card pad">${this._body(t)}</div>`;
  }

  private _body(t: Text) {
    if (!this._levels) {
      return this._error
        ? html`<p class="error" role="alert">${this._error}</p>`
        : html`<span class="muted small">${t.loading}</span>`;
    }
    const levels: RoomLevels = { ...this._levels, ...this._save?.changes };
    const warmer = (["night", "eco"] as const).filter(
      (level) => levels[`${level}_temperature`] > levels.comfort_temperature,
    );
    return html`
      ${LEVELS.map((level) => this._temperatureRow(t, levels, level))}
      ${warmer.map(
        (level) => html`<p class="hint small" role="status">${format(t.warmer, { level: t[level] })}</p>`,
      )}
      ${stepper({
        label: t.leadTime,
        value: formatLeadTime(levels.lead_time_minutes),
        less: format(t.less, { name: t.leadTime }),
        more: format(t.more, { name: t.leadTime }),
        canDown: levels.lead_time_minutes > 0,
        canUp: levels.lead_time_minutes < MAX_LEAD_TIME_MINUTES,
        onStep: (direction) =>
          this._change({ lead_time_minutes: stepLeadTime(levels.lead_time_minutes, direction) }),
      })}
      <p class="muted small note">${t.leadTimeNote}</p>
      ${this._error ? html`<p class="error small" role="alert">${this._error}</p>` : nothing}
    `;
  }

  private _temperatureRow(t: Text, levels: RoomLevels, level: Level) {
    const key: TemperatureKey = `${level}_temperature`;
    const value = levels[key];
    return stepper({
      label: html`<i class="dot dot-${level}"></i>${t[level]}`,
      value: formatTemperature(this.hass, value),
      less: format(t.less, { name: t[level] }),
      more: format(t.more, { name: t[level] }),
      canDown: value > MIN_TEMPERATURE,
      canUp: value < MAX_TEMPERATURE,
      onStep: (direction) => this._change({ [key]: stepTemperature(value, direction) }),
    });
  }

  private _change(changes: Partial<RoomLevels>): void {
    this._error = undefined;
    this._save?.change(changes);
    this.requestUpdate();
  }

  static override styles = [
    sharedStyles,
    stepperStyles,
    css`
      .dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
      }
      .dot-comfort {
        background: #ffb300;
      }
      .dot-night {
        background: var(--cc-night);
      }
      .dot-eco {
        background: #8bc34a;
      }
      .note {
        margin: 4px 0 0;
      }
    `,
  ];
}

defineOnce("cc-room-levels-section", RoomLevelsSection);
