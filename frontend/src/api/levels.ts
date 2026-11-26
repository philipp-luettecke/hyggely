// Panel API, ticket 19: level temperatures and lead time of a room, global
// temperatures for away, vacation and frost protection.

import type { HomeAssistant } from "../types";

export interface RoomLevels {
  comfort_temperature: number;
  night_temperature: number;
  eco_temperature: number;
  lead_time_minutes: number;
}

export interface GlobalTemperatures {
  away_temperature: number;
  vacation_temperature: number;
  frost_temperature: number;
}

export function getRoomLevels(hass: HomeAssistant, roomId: string): Promise<RoomLevels> {
  return hass.callWS<RoomLevels>({ type: "hyggely/room/levels", room_id: roomId });
}

/** Change the levels given; the room applies them at once. */
export function setRoomLevels(
  hass: HomeAssistant,
  roomId: string,
  changes: Partial<RoomLevels>,
): Promise<null> {
  return hass.callWS<null>({
    type: "hyggely/room/set_levels",
    room_id: roomId,
    ...changes,
  });
}

export function getGlobalTemperatures(hass: HomeAssistant): Promise<GlobalTemperatures> {
  return hass.callWS<GlobalTemperatures>({ type: "hyggely/house/temperatures" });
}

/** Change the global temperatures given; all rooms apply them at once. */
export function setGlobalTemperatures(
  hass: HomeAssistant,
  changes: Partial<GlobalTemperatures>,
): Promise<null> {
  return hass.callWS<null>({ type: "hyggely/house/set_temperatures", ...changes });
}
