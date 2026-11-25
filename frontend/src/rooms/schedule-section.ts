// Rooms tab, section of ticket 18: which schedule helper applies to the room,
// then its week (mini bar per day) and the chosen day as a timeline. Every
// change is saved at once through the native `schedule/update`; new helpers are
// created through `schedule/create`, unused ones deleted through
// `schedule/delete`. Assignments go through the Panel API.

import { LitElement, css, html, nothing, type PropertyDeclarations, type PropertyValues } from "lit";
import { live } from "lit/directives/live.js";
import type { RoomOverview } from "../api/rooms";
import {
  assignSchedule,
  createSchedule,
  deleteSchedule,
  listSchedules,
  subscribeAssignments,
  updateSchedule,
  type ScheduleAssignments,
  type ScheduleHelper,
  type ScheduleItem,
} from "../api/schedules";
import { errorMessage, format, localize } from "../i18n";
import { sharedStyles } from "../styles";
import type { HomeAssistant, Unsubscribe } from "../types";
import { defineOnce } from "../define";
import "./create-schedule-sheet";
import type { CopySource, CreateRequest } from "./create-schedule-sheet";
import "./schedule-timeline";
import type { WeekChange } from "./schedule-timeline";
import { scheduleWeekOf, today, weekOf, type Week } from "./schedule-week";

const NEW_SCHEDULE = "__new__";

const TEXTS = {
  de: {
    title: "Zeitplan",
    loading: "Lade Zeitpläne …",
    schedule: "Zeitplan",
    none: "– kein Zeitplan –",
    create: "+ Neuen Zeitplan anlegen …",
    noSchedule: "{room} hat keinen Zeitplan und hält Eco.",
    createButton: "Zeitplan anlegen",
    missing: "Der Zeitplan-Helfer {entity} fehlt oder ist nicht verfügbar. {room} hält Eco, bis du einen Zeitplan zuweist oder anlegst.",
    notEditable:
      "„{name}“ ist nicht in der Oberfläche angelegt (z. B. in YAML) und lässt sich hier nicht bearbeiten. Weise einen anderen Zeitplan zu oder lege einen neuen an.",
    sharedWith: "gilt auch für {rooms}",
    sharedWarning: "Jede Änderung wirkt sofort auf {count} Räume.",
    split: "Für {room} abtrennen",
    comfort: "Komfort",
    night: "Nacht",
    eco: "Eco (außerhalb der Blöcke)",
    saved: "Gespeichert: {change}",
    skipped: "Nicht kopiert nach {days}: überschneidet sich dort mit einem vorhandenen Block.",
    failed: "Nicht gespeichert: ",
    days: "Mo,Di,Mi,Do,Fr,Sa,So",
    orphanQuestion: "„{name}“ gilt für keinen Raum mehr – löschen?",
    delete: "Löschen",
    keep: "Behalten",
    deleted: "„{name}“ gelöscht.",
  },
  en: {
    title: "Schedule",
    loading: "Loading schedules …",
    schedule: "Schedule",
    none: "– no schedule –",
    create: "+ Create new schedule …",
    noSchedule: "{room} has no schedule and holds eco.",
    createButton: "Create schedule",
    missing: "The schedule helper {entity} is missing or unavailable. {room} holds eco until you assign or create a schedule.",
    notEditable:
      "“{name}” was not created in the UI (e.g. in YAML) and cannot be edited here. Assign another schedule or create a new one.",
    sharedWith: "also applies to {rooms}",
    sharedWarning: "Every change applies at once to {count} rooms.",
    split: "Split off for {room}",
    comfort: "Comfort",
    night: "Night",
    eco: "Eco (outside the blocks)",
    saved: "Saved: {change}",
    skipped: "Not copied to {days}: it overlaps a block there.",
    failed: "Not saved: ",
    days: "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
    orphanQuestion: "“{name}” applies to no room any more – delete it?",
    delete: "Delete",
    keep: "Keep",
    deleted: "“{name}” deleted.",
  },
};

type Text = (typeof TEXTS)["de"];

interface CreateSheet {
  preselect?: string;
  busy: boolean;
  error?: string;
}

interface Orphan {
  scheduleId: string;
  name: string;
}

export class RoomScheduleSection extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    room: { attribute: false },
    _assignments: { state: true },
    _items: { state: true },
    _edited: { state: true },
    _day: { state: true },
    _sheet: { state: true },
    _orphan: { state: true },
    _status: { state: true },
    _error: { state: true },
  };

  hass?: HomeAssistant;
  room?: RoomOverview;
  private _assignments?: ScheduleAssignments;
  /** Items of `schedule/list` by id. */
  private _items?: Map<string, ScheduleItem>;
  /** The week as edited but maybe not saved yet, per schedule id. */
  private _edited = new Map<string, Week>();
  private _day = today();
  private _sheet?: CreateSheet;
  private _orphan?: Orphan;
  private _status?: string;
  private _error?: string;
  private _saving = new Map<string, Promise<unknown>>();
  private _unsubscribe?: Promise<Unsubscribe>;

  override connectedCallback(): void {
    super.connectedCallback();
    this._subscribe();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubscribe?.then((unsubscribe) => unsubscribe()).catch(() => undefined);
    this._unsubscribe = undefined;
  }

  protected override willUpdate(changed: PropertyValues): void {
    const previous = changed.get("room") as RoomOverview | undefined;
    if (changed.has("room") && previous?.room_id !== this.room?.room_id) {
      this._day = today();
      this._sheet = undefined;
      this._status = undefined;
    }
  }

  protected override updated(changed: PropertyValues): void {
    if (changed.has("hass")) {
      this._subscribe();
    }
  }

  private _subscribe(): void {
    if (!this.hass || !this.isConnected || this._unsubscribe) {
      return;
    }
    this._unsubscribe = subscribeAssignments(this.hass, (assignments) => {
      this._assignments = assignments;
      void this._reload();
    });
    this._unsubscribe.catch((error: unknown) => {
      this._unsubscribe = undefined;
      this._error = errorMessage(error);
    });
  }

  private async _reload(): Promise<void> {
    if (!this.hass) {
      return;
    }
    try {
      const items = await listSchedules(this.hass);
      this._items = new Map(items.map((item) => [item.id, item]));
    } catch (error: unknown) {
      this._error = errorMessage(error);
    }
  }

  protected override render() {
    const t = localize(this.hass, TEXTS);
    const room = this.room;
    const assignments = this._assignments;
    if (!room || !assignments || !this._items) {
      return html`<h2 class="section">${t.title}</h2>
        <div class="card pad muted small">${this._error ?? t.loading}</div>`;
    }
    const entityId = assignments.rooms.find((candidate) => candidate.room_id === room.room_id)?.entity_id ?? null;
    const helper = assignments.schedules.find((candidate) => candidate.entity_id === entityId);
    return html`
      <h2 class="section">${t.title}</h2>
      ${this._assignmentCard(room, entityId, helper, t)} ${this._body(room, entityId, helper, t)}
      ${this._status ? html`<p class="status small" role="status">${this._status}</p>` : nothing}
      ${this._orphanCard(t)} ${this._sheetView(room)}
    `;
  }

  private _assignmentCard(room: RoomOverview, entityId: string | null, helper: ScheduleHelper | undefined, t: Text) {
    const schedules = this._assignments?.schedules ?? [];
    const others = entityId
      ? (this._assignments?.rooms ?? []).filter((r) => r.entity_id === entityId && r.room_id !== room.room_id)
      : [];
    const item = this._item(helper);
    return html`<div class="card pad">
      <label class="field"
        >${t.schedule}
        <select .value=${live(entityId ?? "")} @change=${this._choose}>
          <option value="" ?selected=${entityId === null}>${t.none}</option>
          ${schedules.map(
            (schedule) => html`<option value=${schedule.entity_id} ?selected=${schedule.entity_id === entityId}>
              ${schedule.name}
            </option>`,
          )}
          ${entityId && !helper ? html`<option value=${entityId} selected>${entityId}</option>` : nothing}
          <option value=${NEW_SCHEDULE}>${t.create}</option>
        </select>
      </label>
      ${others.length > 0
        ? html`<div class="shared">
            <div><b>${format(t.sharedWith, { rooms: others.map((r) => r.name).join(", ") })}</b></div>
            <div class="small">${format(t.sharedWarning, { count: String(others.length + 1) })}</div>
            ${item
              ? html`<button class="btn small" @click=${() => this._openSheet(item.id)}>
                  ${format(t.split, { room: room.name })}
                </button>`
              : nothing}
          </div>`
        : nothing}
      ${this._error ? html`<p class="err" role="alert">${this._error}</p>` : nothing}
    </div>`;
  }

  private _body(room: RoomOverview, entityId: string | null, helper: ScheduleHelper | undefined, t: Text) {
    if (entityId === null || !helper) {
      const text =
        entityId === null
          ? format(t.noSchedule, { room: room.name })
          : format(t.missing, { entity: entityId, room: room.name });
      return html`<div class="card pad">
        <p class="muted">${text}</p>
        <button class="btn primary" @click=${() => this._openSheet()}>${t.createButton}</button>
      </div>`;
    }
    const item = this._item(helper);
    if (!item) {
      return html`<div class="card pad muted small">${format(t.notEditable, { name: helper.name })}</div>`;
    }
    return html`
      ${this._legend(t)}
      <cc-schedule-timeline
        .hass=${this.hass}
        .week=${this._edited.get(item.id) ?? weekOf(item)}
        .day=${this._day}
        @cc-day-change=${(event: CustomEvent<number>) => (this._day = event.detail)}
        @cc-week-change=${(event: CustomEvent<WeekChange>) => this._save(item, event.detail)}
      ></cc-schedule-timeline>
    `;
  }

  private _legend(t: Text) {
    return html`<div class="legend small">
      <span><i class="lvl-comfort"></i>${t.comfort}</span>
      <span><i class="lvl-night"></i>${t.night}</span>
      <span><i class="lvl-eco"></i>${t.eco}</span>
    </div>`;
  }

  private _orphanCard(t: Text) {
    const orphan = this._orphan;
    if (!orphan) {
      return nothing;
    }
    return html`<div class="card pad orphan" role="alertdialog">
      <p>${format(t.orphanQuestion, { name: orphan.name })}</p>
      <div class="actions">
        <span class="spacer"></span>
        <button class="btn" @click=${() => (this._orphan = undefined)}>${t.keep}</button>
        <button class="btn danger" @click=${this._deleteOrphan}>${t.delete}</button>
      </div>
    </div>`;
  }

  private _sheetView(room: RoomOverview) {
    const sheet = this._sheet;
    if (!sheet) {
      return nothing;
    }
    const sources: CopySource[] = [...(this._items?.values() ?? [])]
      .map((item) => ({ id: item.id, name: item.name, week: this._edited.get(item.id) ?? weekOf(item) }))
      .sort((a, b) => a.name.localeCompare(b.name));
    return html`<cc-create-schedule-sheet
      .hass=${this.hass}
      .roomName=${room.name}
      .takenNames=${(this._assignments?.schedules ?? []).map((schedule) => schedule.name)}
      .sources=${sources}
      .preselect=${sheet.preselect}
      .busy=${sheet.busy}
      .error=${sheet.error}
      @cc-cancel=${() => (this._sheet = undefined)}
      @cc-create=${(event: CustomEvent<CreateRequest>) => this._create(room, event.detail)}
    ></cc-create-schedule-sheet>`;
  }

  /** The editable item of a helper; undefined for one the native commands do not know. */
  private _item(helper: ScheduleHelper | undefined): ScheduleItem | undefined {
    return helper?.schedule_id ? this._items?.get(helper.schedule_id) : undefined;
  }

  private _openSheet(preselect?: string): void {
    this._sheet = { preselect, busy: false };
  }

  private _choose = (event: Event): void => {
    const select = event.target as HTMLSelectElement;
    const room = this.room;
    if (!room) {
      return;
    }
    if (select.value === NEW_SCHEDULE) {
      this._openSheet();
      return;
    }
    void this._assign(room, { entityId: select.value || null });
  };

  private async _assign(
    room: RoomOverview,
    schedule: { entityId: string | null } | { scheduleId: string },
  ): Promise<boolean> {
    if (!this.hass) {
      return false;
    }
    const previous = this._helperOf(room.room_id);
    this._error = undefined;
    this._status = undefined;
    try {
      await assignSchedule(this.hass, room.room_id, schedule);
    } catch (error: unknown) {
      this._error = errorMessage(error);
      this.requestUpdate();
      return false;
    }
    this._offerDelete(room.room_id, previous);
    return true;
  }

  private _helperOf(roomId: string): ScheduleHelper | undefined {
    const entityId = this._assignments?.rooms.find((r) => r.room_id === roomId)?.entity_id;
    return this._assignments?.schedules.find((schedule) => schedule.entity_id === entityId);
  }

  /** Ask once to delete the previous schedule of the room when no other room uses it. */
  private _offerDelete(roomId: string, previous: ScheduleHelper | undefined): void {
    const item = this._item(previous);
    if (!previous || !item) {
      return;
    }
    const stillUsed = this._assignments?.rooms.some((r) => r.room_id !== roomId && r.entity_id === previous.entity_id);
    if (!stillUsed) {
      this._orphan = { scheduleId: item.id, name: item.name };
    }
  }

  private _deleteOrphan = async (): Promise<void> => {
    const orphan = this._orphan;
    if (!this.hass || !orphan) {
      return;
    }
    const t = localize(this.hass, TEXTS);
    this._orphan = undefined;
    try {
      await deleteSchedule(this.hass, orphan.scheduleId);
      this._status = format(t.deleted, { name: orphan.name });
    } catch (error: unknown) {
      this._error = errorMessage(error);
    }
    await this._reload();
  };

  private async _create(room: RoomOverview, request: CreateRequest): Promise<void> {
    const sheet = this._sheet;
    if (!this.hass || !sheet) {
      return;
    }
    this._sheet = { ...sheet, busy: true, error: undefined };
    let item: ScheduleItem;
    try {
      item = await createSchedule(this.hass, request.name, scheduleWeekOf(request.week));
    } catch (error: unknown) {
      this._sheet = { ...sheet, busy: false, error: errorMessage(error) };
      return;
    }
    this._items = new Map(this._items).set(item.id, item);
    this._sheet = undefined;
    this._day = today();
    await this._assign(room, { scheduleId: item.id });
  }

  /** Show the change at once, save it after the changes before it. */
  private _save(item: ScheduleItem, change: WeekChange): void {
    const hass = this.hass;
    if (!hass) {
      return;
    }
    const t = localize(hass, TEXTS);
    this._edited = new Map(this._edited).set(item.id, change.week);
    const days = t.days.split(",");
    const skipped = change.skipped?.length
      ? ` ${format(t.skipped, { days: change.skipped.map((day) => days[day]).join(", ") })}`
      : "";
    const before = this._saving.get(item.id) ?? Promise.resolve();
    const saving = before
      .catch(() => undefined)
      .then(async () => {
        const current = this._items?.get(item.id) ?? item;
        const saved = await updateSchedule(hass, { ...current, ...scheduleWeekOf(change.week) });
        this._items = new Map(this._items).set(saved.id, saved);
        this._status = format(t.saved, { change: change.label }) + skipped;
      })
      .catch(async (error: unknown) => {
        this._status = t.failed + errorMessage(error);
        await this._reload();
        throw error;
      })
      .finally(() => {
        if (this._saving.get(item.id) === saving) {
          this._saving.delete(item.id);
          const edited = new Map(this._edited);
          edited.delete(item.id);
          this._edited = edited;
        }
      });
    this._saving.set(item.id, saving);
    saving.catch(() => undefined);
  }

  static override styles = [
    sharedStyles,
    css`
      .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
        color: var(--cc-muted);
      }
      select {
        font: inherit;
        font-size: 16px;
        color: var(--primary-text-color);
        background: var(--primary-background-color, #fafafa);
        border: 1px solid var(--cc-divider);
        border-radius: 8px;
        padding: 9px 10px;
      }
      .shared {
        margin-top: 12px;
        padding: 10px 12px;
        border-radius: 8px;
        background: rgba(230, 81, 0, 0.1);
        border: 1px solid rgba(230, 81, 0, 0.35);
        display: flex;
        flex-direction: column;
        gap: 6px;
        align-items: flex-start;
      }
      .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        margin: 4px 2px 10px;
        color: var(--cc-muted);
      }
      .legend span {
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .legend i {
        width: 14px;
        height: 10px;
        border-radius: 3px;
        display: inline-block;
      }
      .lvl-comfort {
        background: var(--cc-comfort, #ffb74d);
      }
      .lvl-night {
        background: var(--cc-night);
      }
      .lvl-eco {
        background: var(--cc-eco-bg, rgba(139, 195, 74, 0.35));
      }
      .status {
        margin: 8px 2px;
        color: var(--cc-muted);
      }
      .orphan {
        border-color: var(--cc-heat);
      }
      .orphan p {
        margin: 0;
      }
      .actions {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-top: 10px;
      }
      .spacer {
        flex: 1;
      }
      .err {
        color: var(--error-color, #d32f2f);
        font-size: 14px;
        margin: 10px 0 0;
      }
      .btn {
        border: 1px solid var(--cc-divider);
        background: transparent;
        color: var(--primary-text-color);
        border-radius: 8px;
        padding: 8px 12px;
        min-height: 36px;
        font: inherit;
        cursor: pointer;
      }
      .btn.small {
        padding: 6px 10px;
        min-height: 32px;
        font-size: 14px;
      }
      .btn.primary {
        background: var(--cc-primary);
        border-color: transparent;
        color: var(--text-primary-color, #fff);
      }
      .btn.danger {
        color: var(--error-color, #d32f2f);
      }
    `,
  ];
}

defineOnce("cc-room-schedule-section", RoomScheduleSection);
