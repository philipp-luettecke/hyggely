// House tab, section of ticket 20: house mode, vacation with its end and the
// away card with the configured persons.

import { LitElement, type PropertyDeclarations } from "lit";
import { localize } from "../i18n";
import { placeholderSection } from "../placeholder";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";

const TEXTS = {
  de: { title: "Hausbetriebsart, Urlaub und Abwesend" },
  en: { title: "House mode, vacation and away" },
};

export class HouseModeSection extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
  };

  static override styles = sharedStyles;

  hass?: HomeAssistant;

  protected override render() {
    return placeholderSection(this.hass, localize(this.hass, TEXTS).title);
  }
}

defineOnce("cc-house-mode-section", HouseModeSection);
