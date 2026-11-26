// Panel API, ticket 20: house mode, vacation with its end, away with the persons.

import type { HomeAssistant, Unsubscribe } from "../types";

export type HouseMode = "auto" | "vacation" | "off";

export type PersonPresence = "home" | "not_home" | "unknown";

export interface Person {
  entity_id: string;
  name: string;
  presence: PersonPresence;
}

export interface House {
  house_mode: HouseMode;
  /** Local time of Home Assistant with offset, e.g. `2026-11-20T18:00:00+01:00`. */
  vacation_end: string | null;
  away: boolean;
  persons: Person[];
}

/** Call `onHouse` with the house now and after every change. */
export function subscribeHouse(
  hass: HomeAssistant,
  onHouse: (house: House) => void,
): Promise<Unsubscribe> {
  return hass.connection.subscribeMessage<House>(onHouse, {
    type: "hyggely/house/subscribe",
  });
}

/** Switch the house to auto or off; vacation starts with `startVacation`. */
export function setHouseMode(hass: HomeAssistant, houseMode: "auto" | "off"): Promise<null> {
  return hass.callWS<null>({ type: "hyggely/house/set_mode", house_mode: houseMode });
}

/**
 * Start vacation until `end`, local time of Home Assistant without offset,
 * e.g. `2026-11-20T18:00`. During a vacation this moves its end.
 */
export function startVacation(hass: HomeAssistant, end: string): Promise<null> {
  return hass.callWS<null>({ type: "hyggely/house/start_vacation", end });
}

/** Error code of an end that is not in the future. */
export const VACATION_END_MUST_BE_AHEAD = "vacation_end_must_be_ahead";

/** The vacation end as the house reads it, e.g. `Fr. 20.11., 18:00`. */
export function formatVacationEnd(language: string, vacationEnd: string): string {
  // The wall time of Home Assistant, shown as is, whatever zone the phone is in.
  const [date, time] = vacationEnd.slice(0, 16).split("T");
  const [year, month, day] = date.split("-").map(Number);
  const [hour, minute] = time.split(":").map(Number);
  return new Intl.DateTimeFormat(language, {
    timeZone: "UTC",
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(Date.UTC(year, month - 1, day, hour, minute)));
}
