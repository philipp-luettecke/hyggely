// Panel API, ticket 17: room overview and return to auto.
// Each ticket keeps its commands in its own file under `src/api/`.

import type { HomeAssistant, Unsubscribe } from "../types";

export type RoomMode = "auto" | "heat" | "off";

export interface RoomOverview {
  room_id: string;
  name: string;
  current_temperature: number | null;
  target_temperature: number | null;
  room_mode: RoomMode;
  reason: string | null;
  reason_code: string | null;
}

/** Call `onRooms` with all rooms now and after every change. */
export function subscribeRooms(
  hass: HomeAssistant,
  onRooms: (rooms: RoomOverview[]) => void,
): Promise<Unsubscribe> {
  return hass.connection.subscribeMessage<{ rooms: RoomOverview[] }>(
    (message) => onRooms(message.rooms),
    { type: "climate_control/rooms/subscribe" },
  );
}

/** End the override or off of a room: it follows its schedule again. */
export function returnToAuto(hass: HomeAssistant, roomId: string): Promise<null> {
  return hass.callWS<null>({
    type: "climate_control/room/return_to_auto",
    room_id: roomId,
  });
}
