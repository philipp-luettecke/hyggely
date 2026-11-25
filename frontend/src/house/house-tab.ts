// House tab: the section of ticket 20 (house mode, vacation, away) and the
// section of ticket 19 (global temperatures), each in its own file.

import { LitElement, html, type PropertyDeclarations } from "lit";
import type { HomeAssistant } from "../types";
import "./global-temperatures-section";
import "./house-mode-section";
import { defineOnce } from "../define";

export class HouseTab extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
  };

  hass?: HomeAssistant;

  protected override render() {
    return html`
      <cc-house-mode-section .hass=${this.hass}></cc-house-mode-section>
      <cc-global-temperatures-section .hass=${this.hass}></cc-global-temperatures-section>
    `;
  }
}

defineOnce("cc-house-tab", HouseTab);
