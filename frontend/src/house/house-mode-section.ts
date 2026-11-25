// House tab, section of ticket 20: house mode, vacation with its end and the
// away card with the configured persons. Vacation starts only once its end is
// chosen in a sheet; during a vacation the end stays changeable there.

import { LitElement, css, html, nothing, type PropertyDeclarations, type PropertyValues } from "lit";
import {
  VACATION_END_MUST_BE_AHEAD,
  formatVacationEnd,
  setHouseMode,
  startVacation,
  subscribeHouse,
  type House,
  type HouseMode,
  type PersonPresence,
} from "../api/house";
import { errorMessage, language, localize } from "../i18n";
import { sharedStyles } from "../styles";
import type { HomeAssistant, Unsubscribe } from "../types";
import { defineOnce } from "../define";

const DEFAULT_VACATION_DAYS = 7;
const DEFAULT_VACATION_END_TIME = "18:00";

const TEXTS = {
  de: {
    title: "Hausbetriebsart",
    auto: "Automatik",
    vacation: "Urlaub",
    off: "Aus",
    explainAuto: "Alle Räume folgen ihrem Zeitplan.",
    explainVacation:
      "Alle Räume halten die Urlaubstemperatur. Zum Urlaubsende geht das Haus von selbst zurück auf Automatik.",
    explainOff: "Alle Räume halten Frostschutz.",
    overrideStillWorks: "Eine manuelle Übersteuerung wirkt trotzdem.",
    vacationUntil: "Urlaub bis",
    thenAuto: ", danach Automatik.",
    changeEnd: "Ende ändern",
    sheetStart: "Urlaub",
    sheetChange: "Urlaubsende ändern",
    sheetHint: "Bis zum Ende halten alle Räume die Urlaubstemperatur, danach Automatik.",
    endDate: "Urlaub endet am",
    endTime: "um",
    start: "Urlaub starten",
    save: "Speichern",
    cancel: "Abbrechen",
    endNotAhead: "Das Urlaubsende muss in der Zukunft liegen.",
    failed: "Die Heizungssteuerung hat abgelehnt: ",
    awayTitle: "Abwesend",
    yes: "Ja",
    no: "Nein",
    awayNow: "Niemand ist zu Hause. Räume ohne Übersteuerung halten die Abwesend-Temperatur.",
    notAway: "Mindestens eine Person ist zu Hause.",
    awayExplain:
      "Abwesend ist keine Hausbetriebsart, sondern folgt aus der Anwesenheit: alle Personen länger als die Abwesenheitsverzögerung weg.",
    noPersons: "Keine Personen eingerichtet, Abwesend wirkt nie. Personen legst du in den Optionen der Integration fest.",
    home: "zu Hause",
    not_home: "unterwegs",
    unknown: "unbekannt – zählt als zu Hause",
    loading: "Lade Haus …",
  },
  en: {
    title: "House mode",
    auto: "Automatic",
    vacation: "Vacation",
    off: "Off",
    explainAuto: "All rooms follow their schedule.",
    explainVacation:
      "All rooms hold the vacation temperature. At the vacation end the house returns to automatic by itself.",
    explainOff: "All rooms hold frost protection.",
    overrideStillWorks: "A manual override still works.",
    vacationUntil: "Vacation until",
    thenAuto: ", then automatic.",
    changeEnd: "Change end",
    sheetStart: "Vacation",
    sheetChange: "Change vacation end",
    sheetHint: "Until the end all rooms hold the vacation temperature, then automatic.",
    endDate: "Vacation ends on",
    endTime: "at",
    start: "Start vacation",
    save: "Save",
    cancel: "Cancel",
    endNotAhead: "The vacation end must be in the future.",
    failed: "The heating control refused: ",
    awayTitle: "Away",
    yes: "Yes",
    no: "No",
    awayNow: "Nobody is home. Rooms without an override hold the away temperature.",
    notAway: "At least one person is home.",
    awayExplain:
      "Away is not a house mode; it follows from presence: all persons gone for longer than the presence delay.",
    noPersons: "No persons set up, so the house is never away. Choose persons in the options of the integration.",
    home: "home",
    not_home: "away",
    unknown: "unknown – counts as home",
    loading: "Loading house …",
  },
};

type Text = (typeof TEXTS)["de"];

const MODES: HouseMode[] = ["auto", "vacation", "off"];

interface VacationSheet {
  date: string;
  time: string;
  busy: boolean;
  error?: string;
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/** Date and time to suggest: the stored end if still ahead, else in 7 days at 18:00. */
function suggestedEnd(house: House): { date: string; time: string } {
  if (house.vacation_end && new Date(house.vacation_end).getTime() > Date.now()) {
    const [date, time] = house.vacation_end.slice(0, 16).split("T");
    return { date, time };
  }
  const day = new Date();
  day.setDate(day.getDate() + DEFAULT_VACATION_DAYS);
  return {
    date: `${day.getFullYear()}-${pad(day.getMonth() + 1)}-${pad(day.getDate())}`,
    time: DEFAULT_VACATION_END_TIME,
  };
}

export class HouseModeSection extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    _house: { state: true },
    _sheet: { state: true },
    _error: { state: true },
  };

  hass?: HomeAssistant;
  private _house?: House;
  private _sheet?: VacationSheet;
  private _error?: string;
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

  protected override updated(changed: PropertyValues): void {
    if (changed.has("hass")) {
      this._subscribe();
    }
  }

  private _subscribe(): void {
    if (!this.hass || !this.isConnected || this._unsubscribe) {
      return;
    }
    this._unsubscribe = subscribeHouse(this.hass, (house) => (this._house = house));
    this._unsubscribe.catch((error: unknown) => {
      this._unsubscribe = undefined;
      this._error = errorMessage(error);
    });
  }

  protected override render() {
    const t = localize(this.hass, TEXTS);
    const house = this._house;
    if (!house) {
      return html`<h2 class="section">${t.title}</h2>
        <div class="card pad muted small">${this._error ?? t.loading}</div>`;
    }
    return html`
      <h2 class="section">${t.title}</h2>
      ${this._modeCard(house, t)} ${this._awayCard(house, t)} ${this._vacationSheet(house, t)}
    `;
  }

  private _modeCard(house: House, t: Text) {
    const explain = {
      auto: t.explainAuto,
      vacation: t.explainVacation,
      off: t.explainOff,
    }[house.house_mode];
    return html`<div class="card pad">
      <div class="seg" role="group" aria-label=${t.title}>
        ${MODES.map(
          (mode) => html`<button
            class=${house.house_mode === mode ? "on" : ""}
            aria-pressed=${house.house_mode === mode ? "true" : "false"}
            @click=${() => this._choose(mode)}
          >
            ${t[mode]}
          </button>`,
        )}
      </div>
      <p class="muted small">${explain} ${t.overrideStillWorks}</p>
      ${house.house_mode === "vacation" && house.vacation_end
        ? html`<div class="row-between">
            <span
              >${t.vacationUntil}
              <b>${formatVacationEnd(language(this.hass), house.vacation_end)}</b>${t.thenAuto}</span
            >
            <button class="btn" @click=${this._openSheet}>${t.changeEnd}</button>
          </div>`
        : nothing}
      ${this._error ? html`<p class="err" role="alert">${this._error}</p>` : nothing}
    </div>`;
  }

  private _awayCard(house: House, t: Text) {
    return html`<div class="card pad">
      <div class="row-between">
        <b>${t.awayTitle}</b>
        <span class="chip static ${house.away ? "selected warn" : ""}">
          ${house.away ? t.yes : t.no}
        </span>
      </div>
      <p class="muted small">${house.away ? t.awayNow : t.notAway} ${t.awayExplain}</p>
      ${house.persons.length === 0
        ? html`<p class="muted small">${t.noPersons}</p>`
        : html`<ul class="persons">
            ${house.persons.map(
              (person) => html`<li>
                <span>${person.name}</span>
                <span class="presence presence-${person.presence}"
                  >${t[person.presence satisfies PersonPresence]}</span
                >
              </li>`,
            )}
          </ul>`}
    </div>`;
  }

  private _vacationSheet(house: House, t: Text) {
    const sheet = this._sheet;
    if (!sheet) {
      return nothing;
    }
    const onVacation = house.house_mode === "vacation";
    return html`<div class="sheet-root">
      <div class="backdrop" @click=${this._closeSheet}></div>
      <div class="sheet" role="dialog" aria-modal="true" aria-labelledby="sheet-title">
        <h3 id="sheet-title">${onVacation ? t.sheetChange : t.sheetStart}</h3>
        <p class="muted small">${t.sheetHint}</p>
        <div class="field-row">
          <label
            >${t.endDate}
            <input
              type="date"
              .value=${sheet.date}
              @input=${(event: Event) => this._editSheet({ date: (event.target as HTMLInputElement).value })}
          /></label>
          <label
            >${t.endTime}
            <input
              type="time"
              .value=${sheet.time}
              @input=${(event: Event) => this._editSheet({ time: (event.target as HTMLInputElement).value })}
          /></label>
        </div>
        ${sheet.error ? html`<p class="err" role="alert">${sheet.error}</p>` : nothing}
        <div class="sheet-actions">
          <span class="spacer"></span>
          <button class="btn" @click=${this._closeSheet}>${t.cancel}</button>
          <button
            class="btn primary"
            ?disabled=${sheet.busy || !sheet.date || !sheet.time}
            @click=${this._submitSheet}
          >
            ${onVacation ? t.save : t.start}
          </button>
        </div>
      </div>
    </div>`;
  }

  private _choose(mode: HouseMode): void {
    const house = this._house;
    if (!this.hass || !house) {
      return;
    }
    this._error = undefined;
    if (mode === "vacation") {
      this._openSheet();
      return;
    }
    if (mode === house.house_mode) {
      return;
    }
    const t = localize(this.hass, TEXTS);
    setHouseMode(this.hass, mode).catch((error: unknown) => {
      this._error = t.failed + errorMessage(error);
    });
  }

  private _openSheet = (): void => {
    if (this._house) {
      this._sheet = { ...suggestedEnd(this._house), busy: false };
    }
  };

  private _closeSheet = (): void => {
    this._sheet = undefined;
  };

  private _editSheet(change: Partial<VacationSheet>): void {
    if (this._sheet) {
      this._sheet = { ...this._sheet, ...change, error: undefined };
    }
  }

  private _submitSheet = async (): Promise<void> => {
    const sheet = this._sheet;
    if (!this.hass || !sheet) {
      return;
    }
    const t = localize(this.hass, TEXTS);
    this._sheet = { ...sheet, busy: true, error: undefined };
    try {
      await startVacation(this.hass, `${sheet.date}T${sheet.time}`);
      this._sheet = undefined;
    } catch (error: unknown) {
      const code = (error as { code?: unknown } | null)?.code;
      this._sheet = {
        ...sheet,
        busy: false,
        error: code === VACATION_END_MUST_BE_AHEAD ? t.endNotAhead : t.failed + errorMessage(error),
      };
    }
  };

  static override styles = [
    sharedStyles,
    css`
      .seg {
        display: flex;
        border: 1px solid var(--cc-divider);
        border-radius: 10px;
        overflow: hidden;
      }
      .seg button {
        flex: 1;
        padding: 14px 6px;
        border: 0;
        background: transparent;
        color: var(--primary-text-color);
        font: inherit;
        font-weight: 500;
        cursor: pointer;
      }
      .seg button + button {
        border-left: 1px solid var(--cc-divider);
      }
      .seg button.on {
        background: var(--cc-primary);
        color: var(--text-primary-color, #fff);
      }
      .row-between {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
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
      .chip.static {
        cursor: default;
      }
      .chip.selected.warn {
        background: var(--cc-heat);
      }
      .err {
        color: var(--error-color, #d32f2f);
        font-size: 14px;
        margin: 10px 0 0;
      }
      ul.persons {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      ul.persons li {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        padding: 8px 0;
        border-top: 1px solid var(--cc-divider);
      }
      .presence-not_home {
        color: var(--cc-night);
      }
      .presence-unknown {
        color: var(--cc-muted);
      }
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
        margin: 0 0 4px;
        font-size: 18px;
        font-weight: 500;
      }
      .field-row {
        display: flex;
        gap: 12px;
      }
      .field-row label {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
        color: var(--cc-muted);
        margin: 10px 0;
      }
      .field-row input {
        font: inherit;
        font-size: 16px;
        color: var(--primary-text-color);
        background: var(--primary-background-color, #fafafa);
        border: 1px solid var(--cc-divider);
        border-radius: 8px;
        padding: 9px 10px;
        min-width: 0;
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

defineOnce("cc-house-mode-section", HouseModeSection);
