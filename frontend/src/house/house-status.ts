// Overview, chips of ticket 20 above the rooms: house mode (with the vacation
// end) and away; a tap leads to the house tab.

import { LitElement, css, html, nothing, type PropertyDeclarations, type PropertyValues } from "lit";
import { formatVacationEnd, subscribeHouse, type House } from "../api/house";
import { format, language, localize } from "../i18n";
import { navigate } from "../navigation";
import { sharedStyles } from "../styles";
import type { HomeAssistant, Unsubscribe } from "../types";
import { defineOnce } from "../define";

const TEXTS = {
  de: {
    auto: "Haus: Automatik",
    vacation: "Haus: Urlaub bis {end}",
    off: "Haus: Aus",
    away: "Abwesend",
    someoneHome: "Jemand zu Hause",
  },
  en: {
    auto: "House: automatic",
    vacation: "House: vacation until {end}",
    off: "House: off",
    away: "Away",
    someoneHome: "Someone at home",
  },
};

export class HouseStatus extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    _house: { state: true },
  };

  hass?: HomeAssistant;
  private _house?: House;
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
    this._unsubscribe.catch(() => (this._unsubscribe = undefined));
  }

  protected override render() {
    const house = this._house;
    if (!house) {
      return nothing;
    }
    const t = localize(this.hass, TEXTS);
    const mode =
      house.house_mode === "vacation" && house.vacation_end
        ? format(t.vacation, { end: formatVacationEnd(language(this.hass), house.vacation_end) })
        : house.house_mode === "off"
          ? t.off
          : t.auto;
    return html`<div class="chips">
      <button
        class="chip ${house.house_mode === "auto" ? "" : "selected warn"}"
        @click=${this._openHouse}
      >
        ${mode}
      </button>
      <button class="chip ${house.away ? "selected warn" : ""}" @click=${this._openHouse}>
        ${house.away ? t.away : t.someoneHome}
      </button>
    </div>`;
  }

  private _openHouse = (): void => navigate(this, "house");

  static override styles = [
    sharedStyles,
    css`
      .chip.selected.warn {
        background: var(--cc-heat);
      }
    `,
  ];
}

defineOnce("cc-house-status", HouseStatus);
