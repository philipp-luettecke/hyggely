// Sheet to create a schedule helper: name, then a template (standard week,
// empty, or a copy of an existing schedule). The schedule section creates and
// assigns it on `cc-create`; it closes the sheet on `cc-cancel`.

import { LitElement, css, html, nothing, type PropertyDeclarations, type PropertyValues } from "lit";
import { format, localize } from "../i18n";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";
import { copyWeek, emptyWeek, standardWeek, type Week } from "./schedule-week";

const TEXTS = {
  de: {
    title: "Neuer Zeitplan für {room}",
    name: "Name",
    defaultName: "Heizung {room}",
    nameTaken: "Diesen Namen hat schon ein Zeitplan.",
    nameMissing: "Bitte einen Namen eingeben.",
    template: "Vorlage",
    standard: "Standardwoche",
    standardHint: "Mo–Fr Komfort 6–8 und 16–21 Uhr, Sa–So 7:30–21 Uhr, nachts Nacht",
    empty: "Leer",
    emptyHint: "Ganztägig Eco, Blöcke legst du danach an",
    copyOf: "Kopie von „{name}“",
    copyHint: "Gleiche Blöcke, danach unabhängig änderbar",
    assigns: "Der neue Zeitplan gilt danach für {room}.",
    cancel: "Abbrechen",
    create: "Anlegen und zuweisen",
  },
  en: {
    title: "New schedule for {room}",
    name: "Name",
    defaultName: "Heating {room}",
    nameTaken: "A schedule with this name exists already.",
    nameMissing: "Please enter a name.",
    template: "Template",
    standard: "Standard week",
    standardHint: "Mon–Fri comfort 6–8 and 16–21, Sat–Sun 7:30–21, night at night",
    empty: "Empty",
    emptyHint: "Eco all day, add blocks afterwards",
    copyOf: "Copy of “{name}”",
    copyHint: "Same blocks, changeable on its own afterwards",
    assigns: "The new schedule then applies to {room}.",
    cancel: "Cancel",
    create: "Create and assign",
  },
};

/** A schedule the new one may copy. */
export interface CopySource {
  id: string;
  name: string;
  week: Week;
}

export interface CreateRequest {
  name: string;
  week: Week;
}

export class CreateScheduleSheet extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    roomName: { attribute: false },
    takenNames: { attribute: false },
    sources: { attribute: false },
    preselect: { attribute: false },
    busy: { attribute: false },
    error: { attribute: false },
    _name: { state: true },
    _template: { state: true },
  };

  hass?: HomeAssistant;
  roomName = "";
  takenNames: string[] = [];
  sources: CopySource[] = [];
  /** Id of the source to copy, e.g. when splitting a shared schedule off. */
  preselect?: string;
  busy = false;
  error?: string;
  private _name?: string;
  /** `standard`, `empty` or the id of a copy source. */
  private _template = "standard";

  protected override willUpdate(changed: PropertyValues): void {
    if (this._name === undefined) {
      this._name = this._suggestedName();
    }
    if (changed.has("preselect") && this.preselect) {
      this._template = this.preselect;
    }
  }

  private _suggestedName(): string {
    const base = format(localize(this.hass, TEXTS).defaultName, { room: this.roomName });
    let name = base;
    for (let index = 2; this._taken(name); index++) {
      name = `${base} ${index}`;
    }
    return name;
  }

  private _taken(name: string): boolean {
    const wanted = name.trim().toLocaleLowerCase();
    return this.takenNames.some((taken) => taken.trim().toLocaleLowerCase() === wanted);
  }

  protected override render() {
    const t = localize(this.hass, TEXTS);
    const name = this._name ?? "";
    const problem = !name.trim() ? t.nameMissing : this._taken(name) ? t.nameTaken : undefined;
    const options = [
      { id: "standard", label: t.standard, hint: t.standardHint },
      { id: "empty", label: t.empty, hint: t.emptyHint },
      ...this.sources.map((source) => ({ id: source.id, label: format(t.copyOf, { name: source.name }), hint: t.copyHint })),
    ];
    return html`<div class="sheet-root">
      <div class="backdrop" @click=${this._cancel}></div>
      <div class="sheet" role="dialog" aria-modal="true" aria-labelledby="create-title">
        <h3 id="create-title">${format(t.title, { room: this.roomName })}</h3>
        <label class="field"
          >${t.name}
          <input .value=${name} @input=${(event: Event) => (this._name = (event.target as HTMLInputElement).value)}
        /></label>
        ${problem ? html`<p class="err small">${problem}</p>` : nothing}
        <div class="field">${t.template}</div>
        <div class="options" role="radiogroup">
          ${options.map(
            (option) => html`<label class="option ${this._template === option.id ? "on" : ""}">
              <input
                type="radio"
                name="template"
                .checked=${this._template === option.id}
                @change=${() => (this._template = option.id)}
              />
              <span><b>${option.label}</b><br /><span class="muted small">${option.hint}</span></span>
            </label>`,
          )}
        </div>
        <p class="muted small">${format(t.assigns, { room: this.roomName })}</p>
        ${this.error ? html`<p class="err" role="alert">${this.error}</p>` : nothing}
        <div class="sheet-actions">
          <span class="spacer"></span>
          <button class="btn" @click=${this._cancel}>${t.cancel}</button>
          <button class="btn primary" ?disabled=${this.busy || problem !== undefined} @click=${this._create}>
            ${t.create}
          </button>
        </div>
      </div>
    </div>`;
  }

  private _week(): Week {
    if (this._template === "standard") {
      return standardWeek();
    }
    const source = this.sources.find((candidate) => candidate.id === this._template);
    return source ? copyWeek(source.week) : emptyWeek();
  }

  private _cancel = (): void => {
    this.dispatchEvent(new CustomEvent("cc-cancel"));
  };

  private _create = (): void => {
    const name = (this._name ?? "").trim();
    if (!name || this._taken(name)) {
      return;
    }
    this.dispatchEvent(new CustomEvent<CreateRequest>("cc-create", { detail: { name, week: this._week() } }));
  };

  static override styles = [
    sharedStyles,
    css`
      .sheet-root {
        position: fixed;
        inset: 0;
        z-index: 50;
      }
      .backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.45);
      }
      .sheet {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        max-height: 88vh;
        overflow: auto;
        background: var(--cc-card);
        color: var(--primary-text-color);
        border-radius: 16px 16px 0 0;
        padding: 18px 16px calc(18px + env(safe-area-inset-bottom));
      }
      .sheet h3 {
        margin: 0 0 8px;
        font-size: 18px;
        font-weight: 500;
      }
      .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
        color: var(--cc-muted);
        margin: 10px 0 6px;
      }
      .field input {
        font: inherit;
        font-size: 16px;
        color: var(--primary-text-color);
        background: var(--primary-background-color, #fafafa);
        border: 1px solid var(--cc-divider);
        border-radius: 8px;
        padding: 9px 10px;
      }
      .options {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .option {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        border: 1px solid var(--cc-divider);
        border-radius: 10px;
        padding: 10px;
        cursor: pointer;
      }
      .option.on {
        border-color: var(--cc-primary);
        box-shadow: 0 0 0 1px var(--cc-primary);
      }
      .err {
        color: var(--error-color, #d32f2f);
        font-size: 14px;
        margin: 6px 0 0;
      }
      .sheet-actions {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-top: 16px;
      }
      .spacer {
        flex: 1;
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
      .btn.primary {
        background: var(--cc-primary);
        border-color: transparent;
        color: var(--text-primary-color, #fff);
      }
      .btn:disabled {
        opacity: 0.45;
        cursor: default;
      }
      @media (min-width: 700px) {
        .sheet {
          left: 50%;
          right: auto;
          bottom: auto;
          top: 50%;
          transform: translate(-50%, -50%);
          width: 460px;
          border-radius: 16px;
        }
      }
    `,
  ];
}

defineOnce("cc-create-schedule-sheet", CreateScheduleSheet);
