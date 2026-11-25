// A section that is not built yet: its title and a short note.

import { html, type TemplateResult } from "lit";
import { localize } from "./i18n";
import type { HomeAssistant } from "./types";

const TEXTS = {
  de: { later: "Folgt in einer späteren Version." },
  en: { later: "Coming in a later version." },
};

export function placeholderSection(
  hass: HomeAssistant | undefined,
  title: string,
): TemplateResult {
  return html`<h2 class="section">${title}</h2>
    <div class="card pad muted small">${localize(hass, TEXTS).later}</div>`;
}
