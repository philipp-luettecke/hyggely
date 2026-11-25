// House tab, section of ticket 19: global temperatures for away, vacation and
// frost protection.

import { LitElement, type PropertyDeclarations } from "lit";
import { localize } from "../i18n";
import { placeholderSection } from "../placeholder";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";

const TEXTS = {
  de: { title: "Temperaturen für das ganze Haus" },
  en: { title: "Temperatures for the whole house" },
};

export class GlobalTemperaturesSection extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
  };

  static override styles = sharedStyles;

  hass?: HomeAssistant;

  protected override render() {
    return placeholderSection(this.hass, localize(this.hass, TEXTS).title);
  }
}

defineOnce("cc-global-temperatures-section", GlobalTemperaturesSection);
