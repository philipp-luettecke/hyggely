// Texts in German and English. Every component keeps its own texts next to it.

import type { HomeAssistant } from "./types";

export type Texts<K extends string> = Record<"de" | "en", Record<K, string>>;

export function language(hass: HomeAssistant | undefined): string {
  return hass?.locale?.language ?? hass?.language ?? "en";
}

export function localize<K extends string>(
  hass: HomeAssistant | undefined,
  texts: Texts<K>,
): Record<K, string> {
  return language(hass).startsWith("de") ? texts.de : texts.en;
}

/** Fill `{name}` placeholders, e.g. `format("{room} kehrt zurück", { room })`. */
export function format(text: string, values: Record<string, string>): string {
  return text.replace(/\{(\w+)\}/g, (match, key: string) => values[key] ?? match);
}

/** The message of an error, also of a failed websocket command. */
export function errorMessage(error: unknown): string {
  const message = (error as { message?: unknown } | null)?.message;
  return typeof message === "string" ? message : String(error);
}

/** A temperature as the house reads it, e.g. `21,5 °C`; a dash if unknown. */
export function formatTemperature(
  hass: HomeAssistant | undefined,
  value: number | null | undefined,
): string {
  if (value === null || value === undefined) {
    return "– °C";
  }
  const number = new Intl.NumberFormat(language(hass), {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);
  return `${number} °C`;
}
