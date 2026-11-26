// Panel API, ticket 18: which schedule applies to which room, and assigning one.
// The schedules themselves are read, written and deleted only through the
// native commands of the schedule helper (`schedule/list|create|update|delete`).

import type { HomeAssistant, Unsubscribe } from "../types";

export const WEEKDAYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
] as const;

export type Weekday = (typeof WEEKDAYS)[number];

/** A block as the schedule helper stores it; times are `HH:MM:SS`, the end up to `24:00:00`. */
export interface ScheduleBlock {
  from: string;
  to: string;
  data?: Record<string, unknown>;
}

export type ScheduleWeek = Record<Weekday, ScheduleBlock[]>;

/** A schedule helper created in the UI, as `schedule/list` returns it. */
export interface ScheduleItem extends Partial<ScheduleWeek> {
  id: string;
  name: string;
  icon?: string;
}

export interface RoomAssignment {
  room_id: string;
  name: string;
  /** The schedule helper of the room; null for a room without schedule. */
  entity_id: string | null;
}

export interface ScheduleHelper {
  entity_id: string;
  /** Id for the native commands; null for a helper they do not know. */
  schedule_id: string | null;
  name: string;
}

export interface ScheduleAssignments {
  rooms: RoomAssignment[];
  /** Every schedule helper, sorted by name; also those of no room. */
  schedules: ScheduleHelper[];
}

/** Error code of a schedule deleted meanwhile. */
export const SCHEDULE_NOT_FOUND = "schedule_not_found";

/** Call `onAssignments` now and whenever rooms are reassigned or helpers change. */
export function subscribeAssignments(
  hass: HomeAssistant,
  onAssignments: (assignments: ScheduleAssignments) => void,
): Promise<Unsubscribe> {
  return hass.connection.subscribeMessage<ScheduleAssignments>(onAssignments, {
    type: "hyggely/schedules/subscribe",
  });
}

/** Give a room a schedule helper, by entity id or by the id `schedule/create` returned; null for none. */
export function assignSchedule(
  hass: HomeAssistant,
  roomId: string,
  schedule: { entityId: string | null } | { scheduleId: string },
): Promise<null> {
  return hass.callWS<null>({
    type: "hyggely/room/assign_schedule",
    room_id: roomId,
    ...("scheduleId" in schedule
      ? { schedule_id: schedule.scheduleId }
      : { entity_id: schedule.entityId }),
  });
}

export function listSchedules(hass: HomeAssistant): Promise<ScheduleItem[]> {
  return hass.callWS<ScheduleItem[]>({ type: "schedule/list" });
}

export function createSchedule(
  hass: HomeAssistant,
  name: string,
  week: ScheduleWeek,
): Promise<ScheduleItem> {
  return hass.callWS<ScheduleItem>({ type: "schedule/create", name, ...week });
}

/** Replace name, icon and all blocks of a schedule. */
export function updateSchedule(hass: HomeAssistant, item: ScheduleItem): Promise<ScheduleItem> {
  const { id, ...fields } = item;
  return hass.callWS<ScheduleItem>({ type: "schedule/update", schedule_id: id, ...fields });
}

export function deleteSchedule(hass: HomeAssistant, scheduleId: string): Promise<null> {
  return hass.callWS<null>({ type: "schedule/delete", schedule_id: scheduleId });
}
