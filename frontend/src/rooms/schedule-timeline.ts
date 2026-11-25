// Week of a schedule as a mini bar per day, below it the chosen day as a
// timeline (variant B). Tap an empty spot for a new block, tap a block to
// select it, then drag its handles or the block itself in steps of 15 minutes.
// Every change goes out at once as a `cc-week-change` event; saving is up to
// the schedule section.

import { LitElement, css, html, nothing, type PropertyDeclarations, type PropertyValues } from "lit";
import { format, localize } from "../i18n";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";
import {
  ALL_DAYS,
  DAY,
  NEW_BLOCK_MINUTES,
  STEP,
  WEEKEND,
  WORKDAYS,
  acrossMidnight,
  clock,
  copyBlock,
  copyDay,
  freeRange,
  nowMinutes,
  room,
  today,
  withDay,
  type Block,
  type Level,
  type Week,
} from "./schedule-week";

const PX_PER_HOUR = 40;
const PX_PER_MINUTE = PX_PER_HOUR / 60;

const TEXTS = {
  de: {
    days: "Mo,Di,Mi,Do,Fr,Sa,So",
    longDays: "Montag,Dienstag,Mittwoch,Donnerstag,Freitag,Samstag,Sonntag",
    comfort: "Komfort",
    night: "Nacht",
    hintIdle: "Block antippen zum Auswählen · leere Stelle antippen für einen neuen Block",
    hintSelected: "Griff oben/unten ziehen ändert Beginn/Ende, den Block selbst ziehen verschiebt ihn (15-Minuten-Raster).",
    toComfort: "Auf Komfort stellen",
    toNight: "Auf Nacht stellen",
    copyBlock: "Kopieren nach …",
    remove: "Löschen",
    done: "Fertig",
    copyDay: "Tag kopieren nach …",
    copyBlockTitle: "{block} kopieren nach:",
    copyDayTitle: "{day} kopieren nach:",
    replaces: "Ersetzt die vorhandenen Blöcke an den gewählten Tagen.",
    workdays: "Mo–Fr",
    weekend: "Sa–So",
    all: "Alle",
    copy: "Kopieren ({count})",
    cancel: "Abbrechen",
    noRoom: "An diesem Tag ist kein Platz mehr frei.",
    continues: "geht weiter bis {day} {time}",
    since: "seit {day} {time}",
    noBlocks: "Keine Blöcke – ganztägig Eco",
  },
  en: {
    days: "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
    longDays: "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday",
    comfort: "Comfort",
    night: "Night",
    hintIdle: "Tap a block to select it · tap an empty spot for a new block",
    hintSelected: "Drag the top/bottom handle to change start/end, drag the block itself to move it (15-minute steps).",
    toComfort: "Set to comfort",
    toNight: "Set to night",
    copyBlock: "Copy to …",
    remove: "Delete",
    done: "Done",
    copyDay: "Copy day to …",
    copyBlockTitle: "Copy {block} to:",
    copyDayTitle: "Copy {day} to:",
    replaces: "Replaces the blocks on the chosen days.",
    workdays: "Mon–Fri",
    weekend: "Sat–Sun",
    all: "All",
    copy: "Copy ({count})",
    cancel: "Cancel",
    noRoom: "There is no free time left on this day.",
    continues: "continues until {day} {time}",
    since: "since {day} {time}",
    noBlocks: "No blocks – eco all day",
  },
};

type Text = (typeof TEXTS)["de"];

export interface WeekChange {
  week: Week;
  /** What changed, e.g. `Mo 07:00–09:00 Komfort`. */
  label: string;
  /** Days a copied block skipped because it would overlap there. */
  skipped?: number[];
}

type DragMode = "move" | "top" | "bottom";

interface Drag {
  mode: DragMode;
  pointerId: number;
  startY: number;
  original: Block;
  lo: number;
  hi: number;
  from: number;
  to: number;
}

interface CopyPanel {
  kind: "block" | "day";
  targets: number[];
}

export class ScheduleTimeline extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    week: { attribute: false },
    day: { attribute: false },
    _selected: { state: true },
    _drag: { state: true },
    _copy: { state: true },
    _note: { state: true },
  };

  hass?: HomeAssistant;
  week: Week = [];
  day = today();
  private _selected?: number;
  private _drag?: Drag;
  private _copy?: CopyPanel;
  private _note?: string;
  private _suppressClick = false;

  protected override willUpdate(changed: PropertyValues): void {
    if (changed.has("day")) {
      this._selected = undefined;
      this._copy = undefined;
      this._note = undefined;
    }
    if (this._selected !== undefined && !this.week[this.day]?.[this._selected]) {
      this._selected = undefined;
    }
  }

  protected override render() {
    const t = localize(this.hass, TEXTS);
    if (this.week.length !== 7) {
      return nothing;
    }
    const days = t.days.split(",");
    const selected = this._selected !== undefined ? this.week[this.day][this._selected] : undefined;
    return html`
      <div class="card week">
        ${days.map(
          (name, day) => html`<button
            class="weekrow ${day === this.day ? "on" : ""}"
            aria-pressed=${day === this.day ? "true" : "false"}
            @click=${() => this._chooseDay(day)}
          >
            <span class="wd ${day === today() ? "today" : ""}">${name}</span>
            <span class="mini">
              ${this.week[day].map(
                (b) =>
                  html`<i
                    class="lvl-${b.level}"
                    style="left:${(b.from / DAY) * 100}%;width:${((b.to - b.from) / DAY) * 100}%"
                  ></i>`,
              )}
            </span>
          </button>`,
        )}
      </div>
      <p class="hint muted small">${selected ? t.hintSelected : t.hintIdle}</p>
      ${selected ? this._toolbar(selected, t) : nothing} ${this._copyPanel(t)}
      ${this._note ? html`<p class="note" role="status">${this._note}</p>` : nothing}
      <div class="card dayview">
        <div class="dayhead">
          <span>${t.longDays.split(",")[this.day]}</span>
          <button class="btn small" @click=${() => this._openCopy("day")}>${t.copyDay}</button>
        </div>
        ${this._edgeHint("top", t)}
        <div class="timeline" style="height:${24 * PX_PER_HOUR}px">
          ${Array.from({ length: 25 }, (_, hour) => html`<div class="hour" style="top:${hour * PX_PER_HOUR}px"><span>${clock(hour * 60)}</span></div>`)}
          <div class="lane" @click=${this._tapLane}>
            ${this.week[this.day].map((b, index) => this._block(b, index, t))}
            ${this.day === today() ? html`<div class="now" style="top:${nowMinutes() * PX_PER_MINUTE}px"></div>` : nothing}
          </div>
        </div>
        ${this._edgeHint("bottom", t)}
        ${this.week[this.day].length === 0 ? html`<p class="muted small center">${t.noBlocks}</p>` : nothing}
      </div>
    `;
  }

  private _block(b: Block, index: number, t: Text) {
    const isSelected = index === this._selected;
    const drag = isSelected ? this._drag : undefined;
    const from = drag ? drag.from : b.from;
    const to = drag ? drag.to : b.to;
    return html`<div
      class="block lvl-${b.level} ${isSelected ? "selected" : ""}"
      style="top:${from * PX_PER_MINUTE}px;height:${(to - from) * PX_PER_MINUTE}px"
      @click=${(event: Event) => this._tapBlock(event, index)}
      @pointerdown=${isSelected ? (event: PointerEvent) => this._startDrag(event, "move") : nothing}
      @pointermove=${isSelected ? this._moveDrag : nothing}
      @pointerup=${isSelected ? this._endDrag : nothing}
      @pointercancel=${isSelected ? this._cancelDrag : nothing}
    >
      ${isSelected
        ? html`<div class="handle top" @pointerdown=${(event: PointerEvent) => this._startDrag(event, "top")}></div>
            <div class="handle bottom" @pointerdown=${(event: PointerEvent) => this._startDrag(event, "bottom")}></div>`
        : nothing}
      <div class="label"><b>${clock(from)} – ${clock(to)}</b> ${t[b.level]}</div>
    </div>`;
  }

  private _edgeHint(edge: "top" | "bottom", t: Text) {
    const blocks = this.week[this.day];
    const index = edge === "top" ? blocks.findIndex((b) => b.from === 0) : blocks.findIndex((b) => b.to === DAY);
    if (index < 0) {
      return nothing;
    }
    const days = t.days.split(",");
    const counterpart = acrossMidnight(this.week, this.day, index);
    if (edge === "top" && counterpart.since) {
      return html`<p class="edge muted small">↑ ${format(t.since, { day: days[counterpart.since.day], time: clock(counterpart.since.from) })}</p>`;
    }
    if (edge === "bottom" && counterpart.continuesUntil) {
      return html`<p class="edge muted small">
        ↓ ${format(t.continues, { day: days[counterpart.continuesUntil.day], time: clock(counterpart.continuesUntil.to) })}
      </p>`;
    }
    return nothing;
  }

  private _toolbar(selected: Block, t: Text) {
    return html`<div class="card toolbar">
      <span><b>${clock(selected.from)} – ${clock(selected.to)}</b> ${t[selected.level]}</span>
      <span class="spacer"></span>
      <button class="btn small" @click=${this._toggleLevel}>${selected.level === "comfort" ? t.toNight : t.toComfort}</button>
      <button class="btn small" @click=${() => this._openCopy("block")}>${t.copyBlock}</button>
      <button class="btn small danger" @click=${this._remove}>${t.remove}</button>
      <button class="btn small primary" @click=${this._done}>${t.done}</button>
    </div>`;
  }

  private _copyPanel(t: Text) {
    const copy = this._copy;
    if (!copy) {
      return nothing;
    }
    const days = t.days.split(",");
    const selected = this._selected !== undefined ? this.week[this.day][this._selected] : undefined;
    const title =
      copy.kind === "block" && selected
        ? format(t.copyBlockTitle, { block: this._describe(this.day, selected, t) })
        : format(t.copyDayTitle, { day: t.longDays.split(",")[this.day] });
    const toggle = (day: number) => {
      const targets = copy.targets.includes(day) ? copy.targets.filter((d) => d !== day) : [...copy.targets, day].sort();
      this._copy = { ...copy, targets };
    };
    const quick = (set: number[]) => (this._copy = { ...copy, targets: set.filter((d) => d !== this.day) });
    return html`<div class="card pad copy">
      <div class="small"><b>${title}</b></div>
      <div class="chips">
        ${days.map((name, day) =>
          day === this.day
            ? nothing
            : html`<button class="chip ${copy.targets.includes(day) ? "selected" : ""}" @click=${() => toggle(day)}>
                ${name}
              </button>`,
        )}
      </div>
      <div class="chips">
        <button class="chip" @click=${() => quick(WORKDAYS)}>${t.workdays}</button>
        <button class="chip" @click=${() => quick(WEEKEND)}>${t.weekend}</button>
        <button class="chip" @click=${() => quick(ALL_DAYS)}>${t.all}</button>
      </div>
      ${copy.kind === "day" ? html`<p class="muted small">${t.replaces}</p>` : nothing}
      <div class="actions">
        <span class="spacer"></span>
        <button class="btn" @click=${() => (this._copy = undefined)}>${t.cancel}</button>
        <button class="btn primary" ?disabled=${copy.targets.length === 0} @click=${this._doCopy}>
          ${format(t.copy, { count: String(copy.targets.length) })}
        </button>
      </div>
    </div>`;
  }

  private _describe(day: number, b: Block, t: Text): string {
    return `${t.days.split(",")[day]} ${clock(b.from)}–${clock(b.to)} ${t[b.level]}`;
  }

  private _chooseDay(day: number): void {
    this.dispatchEvent(new CustomEvent<number>("cc-day-change", { detail: day }));
  }

  private _emit(change: WeekChange): void {
    this.dispatchEvent(new CustomEvent<WeekChange>("cc-week-change", { detail: change }));
  }

  private _tapLane = (event: MouseEvent): void => {
    if (this._suppressClick || event.target !== event.currentTarget) {
      return;
    }
    if (this._selected !== undefined) {
      this._selected = undefined;
      this._copy = undefined;
      return;
    }
    const t = localize(this.hass, TEXTS);
    const lane = event.currentTarget as HTMLElement;
    const minute = Math.floor((event.clientY - lane.getBoundingClientRect().top) / PX_PER_MINUTE / STEP) * STEP;
    const blocks = this.week[this.day];
    const range = freeRange(blocks, minute, NEW_BLOCK_MINUTES);
    if (!range) {
      this._note = t.noRoom;
      return;
    }
    const added: Block = { ...range, level: "comfort", data: {} };
    const week = withDay(this.week, this.day, [...blocks, added]);
    this._selected = week[this.day].findIndex((b) => b.from === added.from);
    this._note = undefined;
    this._emit({ week, label: this._describe(this.day, added, t) });
  };

  private _tapBlock(event: Event, index: number): void {
    event.stopPropagation();
    if (this._suppressClick || this._selected === index) {
      return;
    }
    this._selected = index;
    this._copy = undefined;
    this._note = undefined;
  }

  private _toggleLevel = (): void => {
    const index = this._selected;
    if (index === undefined) {
      return;
    }
    const t = localize(this.hass, TEXTS);
    const blocks = [...this.week[this.day]];
    const level: Level = blocks[index].level === "comfort" ? "night" : "comfort";
    blocks[index] = { ...blocks[index], level };
    this._emit({ week: withDay(this.week, this.day, blocks), label: this._describe(this.day, blocks[index], t) });
  };

  private _remove = (): void => {
    const index = this._selected;
    if (index === undefined) {
      return;
    }
    const t = localize(this.hass, TEXTS);
    const removed = this.week[this.day][index];
    this._selected = undefined;
    this._copy = undefined;
    this._emit({
      week: withDay(
        this.week,
        this.day,
        this.week[this.day].filter((_, i) => i !== index),
      ),
      label: `${this._describe(this.day, removed, t)} ✕`,
    });
  };

  private _done = (): void => {
    this._selected = undefined;
    this._copy = undefined;
  };

  private _openCopy(kind: CopyPanel["kind"]): void {
    this._copy = { kind, targets: [] };
    this._note = undefined;
  }

  private _doCopy = (): void => {
    const copy = this._copy;
    if (!copy || copy.targets.length === 0) {
      return;
    }
    const t = localize(this.hass, TEXTS);
    const days = t.days.split(",");
    const targets = copy.targets.map((d) => days[d]).join(", ");
    this._copy = undefined;
    if (copy.kind === "day") {
      this._emit({
        week: copyDay(this.week, this.day, copy.targets),
        label: `${format(t.copyDayTitle, { day: t.longDays.split(",")[this.day] })} ${targets}`,
      });
      return;
    }
    const index = this._selected;
    if (index === undefined) {
      return;
    }
    const result = copyBlock(this.week, this.day, index, copy.targets);
    this._emit({
      week: result.week,
      label: `${format(t.copyBlockTitle, { block: this._describe(this.day, this.week[this.day][index], t) })} ${targets}`,
      skipped: result.skipped,
    });
  };

  private _startDrag(event: PointerEvent, mode: DragMode): void {
    const index = this._selected;
    if (index === undefined || this._drag) {
      return;
    }
    event.stopPropagation();
    event.preventDefault();
    const blocks = this.week[this.day];
    const original = blocks[index];
    const { lo, hi } = room(blocks, index);
    const target = (event.currentTarget as HTMLElement).closest(".block") as HTMLElement;
    target.setPointerCapture(event.pointerId);
    this._drag = { mode, pointerId: event.pointerId, startY: event.clientY, original, lo, hi, from: original.from, to: original.to };
  }

  private _moveDrag = (event: PointerEvent): void => {
    const drag = this._drag;
    if (!drag || event.pointerId !== drag.pointerId) {
      return;
    }
    const delta = Math.round((event.clientY - drag.startY) / PX_PER_MINUTE / STEP) * STEP;
    let { from, to } = drag.original;
    if (drag.mode === "move") {
      const length = to - from;
      from = Math.min(Math.max(from + delta, drag.lo), drag.hi - length);
      to = from + length;
    } else if (drag.mode === "top") {
      from = Math.min(Math.max(from + delta, drag.lo), to - STEP);
    } else {
      to = Math.max(Math.min(to + delta, drag.hi), from + STEP);
    }
    if (from !== drag.from || to !== drag.to) {
      this._drag = { ...drag, from, to };
    }
  };

  private _endDrag = (event: PointerEvent): void => {
    const drag = this._drag;
    const index = this._selected;
    if (!drag || event.pointerId !== drag.pointerId || index === undefined) {
      return;
    }
    this._drag = undefined;
    if (drag.from === drag.original.from && drag.to === drag.original.to) {
      return;
    }
    this._suppressClick = true;
    window.setTimeout(() => (this._suppressClick = false), 50);
    const t = localize(this.hass, TEXTS);
    const blocks = [...this.week[this.day]];
    blocks[index] = { ...drag.original, from: drag.from, to: drag.to };
    this._emit({ week: withDay(this.week, this.day, blocks), label: this._describe(this.day, blocks[index], t) });
  };

  private _cancelDrag = (): void => {
    this._drag = undefined;
  };

  static override styles = [
    sharedStyles,
    css`
      .lvl-comfort {
        background: var(--cc-comfort, #ffb74d);
        color: #3e2700;
      }
      .lvl-night {
        background: var(--cc-night);
        color: #fff;
      }
      .week {
        padding: 6px;
      }
      .weekrow {
        display: grid;
        grid-template-columns: 34px 1fr;
        align-items: center;
        gap: 8px;
        width: 100%;
        border: 0;
        background: transparent;
        color: var(--primary-text-color);
        font: inherit;
        padding: 6px;
        border-radius: 6px;
        cursor: pointer;
      }
      .weekrow.on {
        background: rgba(3, 169, 244, 0.14);
      }
      .wd {
        text-align: left;
      }
      .wd.today {
        color: var(--cc-primary);
        font-weight: 700;
      }
      .mini {
        position: relative;
        height: 10px;
        border-radius: 5px;
        overflow: hidden;
        background: var(--cc-eco-bg, rgba(139, 195, 74, 0.35));
      }
      .mini i {
        position: absolute;
        top: 0;
        bottom: 0;
      }
      .hint {
        margin: 8px 2px;
      }
      .note {
        margin: 8px 2px;
        color: var(--cc-heat);
        font-size: 14px;
      }
      .toolbar {
        position: sticky;
        top: calc(var(--header-height, 56px) + 50px);
        z-index: 6;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
        padding: 8px 12px;
      }
      .copy .chips {
        margin-top: 8px;
        flex-wrap: wrap;
      }
      .actions {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-top: 8px;
      }
      .spacer {
        flex: 1;
      }
      .dayview {
        padding: 10px 8px 14px 0;
      }
      .dayhead {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        padding: 0 4px 8px 12px;
        font-weight: 500;
      }
      .edge {
        margin: 2px 12px 2px 62px;
      }
      .center {
        text-align: center;
      }
      .timeline {
        position: relative;
        margin: 10px 0;
        user-select: none;
        -webkit-user-select: none;
      }
      .hour {
        position: absolute;
        left: 0;
        right: 0;
        border-top: 1px solid var(--cc-divider);
        pointer-events: none;
      }
      .hour span {
        position: absolute;
        top: -8px;
        left: 6px;
        font-size: 11px;
        color: var(--cc-muted);
        background: var(--cc-card);
        padding-right: 4px;
      }
      .lane {
        position: absolute;
        left: 54px;
        right: 8px;
        top: 0;
        bottom: 0;
        background: var(--cc-eco-bg, rgba(139, 195, 74, 0.18));
        border-radius: 6px;
        cursor: copy;
      }
      .block {
        position: absolute;
        left: 4px;
        right: 4px;
        box-sizing: border-box;
        border-radius: 8px;
        padding: 3px 8px;
        font-size: 13px;
        cursor: pointer;
      }
      .block.selected {
        box-shadow: 0 0 0 3px var(--cc-primary);
        z-index: 3;
        touch-action: none;
        cursor: grab;
      }
      .label {
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
      }
      .handle {
        position: absolute;
        left: 50%;
        width: 64px;
        height: 28px;
        margin-left: -32px;
        z-index: 4;
        touch-action: none;
        cursor: ns-resize;
      }
      .handle::after {
        content: "";
        position: absolute;
        left: 10px;
        right: 10px;
        top: 10px;
        height: 8px;
        border-radius: 4px;
        background: var(--cc-primary);
        border: 2px solid var(--cc-card);
      }
      .handle.top {
        top: -14px;
      }
      .handle.bottom {
        bottom: -14px;
      }
      .now {
        position: absolute;
        left: 0;
        right: 0;
        height: 2px;
        background: #e53935;
        z-index: 2;
        pointer-events: none;
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
      .btn:disabled {
        opacity: 0.45;
        cursor: default;
      }
    `,
  ];
}

defineOnce("cc-schedule-timeline", ScheduleTimeline);
