// Overview, chips of ticket 20 above the rooms: house mode (with the vacation
// end) and away; a tap leads to the house tab. Empty until then.

import { LitElement, nothing, type PropertyDeclarations } from "lit";
import { sharedStyles } from "../styles";
import type { HomeAssistant } from "../types";
import { defineOnce } from "../define";

export class HouseStatus extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
  };

  static override styles = sharedStyles;

  hass?: HomeAssistant;

  protected override render() {
    return nothing;
  }
}

defineOnce("cc-house-status", HouseStatus);
