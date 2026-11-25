// House tab, section of ticket 19: global temperatures for away, vacation and
// frost protection.

import { LitElement, html, nothing, type PropertyDeclarations, type PropertyValues } from "lit";
import { getGlobalTemperatures, setGlobalTemperatures, type GlobalTemperatures } from "../api/levels";
import { errorMessage, format, formatTemperature, localize } from "../i18n";
import {
  DelayedSave,
  MAX_TEMPERATURE,
  MIN_TEMPERATURE,
  stepper,
  stepperStyles,
  stepTemperature,
} from "../stepper";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";

const TEXTS = {
  de: {
    title: "Temperaturen für das ganze Haus",
    away: "Abwesend",
    vacation: "Urlaub",
    frost: "Frostschutz",
    frostNote: "Frostschutz gilt bei offenem Fenster, bei „Aus“ und wenn das Haus aus ist.",
    less: "{name} weniger",
    more: "{name} mehr",
    loading: "Lade Temperaturen …",
    failed: "Konnte nicht gespeichert werden: {error}",
    loadFailed: "Temperaturen konnten nicht geladen werden: {error}",
  },
  en: {
    title: "Temperatures for the whole house",
    away: "Away",
    vacation: "Vacation",
    frost: "Frost protection",
    frostNote: "Frost protection applies with a window open, in “Off” and when the house is off.",
    less: "{name} lower",
    more: "{name} higher",
    loading: "Loading temperatures …",
    failed: "Could not be saved: {error}",
    loadFailed: "Temperatures could not be loaded: {error}",
  },
};

type Text = (typeof TEXTS)["de"];
type GlobalLevel = "away" | "vacation" | "frost";

const GLOBAL_LEVELS: GlobalLevel[] = ["away", "vacation", "frost"];

export class GlobalTemperaturesSection extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    _temperatures: { state: true },
    _error: { state: true },
  };

  static override styles = [sharedStyles, stepperStyles];

  hass?: HomeAssistant;
  private _temperatures?: GlobalTemperatures;
  private _error?: string;
  private _loading = false;
  private _save = new DelayedSave<GlobalTemperatures>((changes) => this._send(changes));

  override connectedCallback(): void {
    super.connectedCallback();
    this._save.connect();
  }

  override disconnectedCallback(): void {
    this._save.disconnect();
    super.disconnectedCallback();
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (changed.has("hass") && !this._temperatures && !this._loading) {
      this._load();
    }
  }

  private _load(): void {
    if (!this.hass) {
      return;
    }
    this._loading = true;
    getGlobalTemperatures(this.hass)
      .then((temperatures) => {
        this._temperatures = temperatures;
        this._error = undefined;
      })
      .catch((error: unknown) => {
        this._error = format(localize(this.hass, TEXTS).loadFailed, { error: errorMessage(error) });
      })
      .finally(() => {
        this._loading = false;
      });
  }

  private _send(changes: Partial<GlobalTemperatures>): void {
    if (!this.hass) {
      return;
    }
    if (this._temperatures) {
      this._temperatures = { ...this._temperatures, ...changes };
    }
    setGlobalTemperatures(this.hass, changes).catch((error: unknown) => {
      this._temperatures = undefined;
      this._load();
      this._error = format(localize(this.hass, TEXTS).failed, { error: errorMessage(error) });
    });
  }

  protected override render() {
    const t = localize(this.hass, TEXTS);
    return html`<h2 class="section">${t.title}</h2>
      <div class="card pad">${this._body(t)}</div>`;
  }

  private _body(t: Text) {
    if (!this._temperatures) {
      return this._error
        ? html`<p class="error" role="alert">${this._error}</p>`
        : html`<span class="muted small">${t.loading}</span>`;
    }
    const temperatures: GlobalTemperatures = { ...this._temperatures, ...this._save.changes };
    return html`
      ${GLOBAL_LEVELS.map((level) => {
        const key = `${level}_temperature` as const;
        const value = temperatures[key];
        return stepper({
          label: t[level],
          value: formatTemperature(this.hass, value),
          less: format(t.less, { name: t[level] }),
          more: format(t.more, { name: t[level] }),
          canDown: value > MIN_TEMPERATURE,
          canUp: value < MAX_TEMPERATURE,
          onStep: (direction) => {
            this._error = undefined;
            this._save.change({ [key]: stepTemperature(value, direction) });
            this.requestUpdate();
          },
        });
      })}
      <p class="muted small">${t.frostNote}</p>
      ${this._error ? html`<p class="error small" role="alert">${this._error}</p>` : nothing}
    `;
  }
}

defineOnce("cc-global-temperatures-section", GlobalTemperaturesSection);
