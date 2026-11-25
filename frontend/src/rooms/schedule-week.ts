// The week of a schedule as the panel edits it: per day (Monday first) the
// blocks in minutes since midnight, each with its level. Pure functions that
// return a new week; the native format stays in `api/schedules.ts`.

import { WEEKDAYS, type ScheduleBlock, type ScheduleItem, type ScheduleWeek } from "../api/schedules";

export const DAY = 24 * 60;
export const STEP = 15;
export const NEW_BLOCK_MINUTES = 60;

/** Level of a block; outside blocks eco applies. */
export type Level = "comfort" | "night";

export interface Block {
  from: number;
  to: number;
  level: Level;
  /** Additional data of the block, kept as it was apart from `level`. */
  data: Record<string, unknown>;
}

export type Week = Block[][];

/** Days as indices, Monday 0. */
export const WORKDAYS = [0, 1, 2, 3, 4];
export const WEEKEND = [5, 6];
export const ALL_DAYS = [0, 1, 2, 3, 4, 5, 6];

function minutes(time: string): number {
  const [hours, mins] = time.split(":").map(Number);
  return hours * 60 + mins;
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/** `HH:MM`, the end of the day as `24:00`. */
export function clock(value: number): string {
  return `${pad(Math.floor(value / 60))}:${pad(value % 60)}`;
}

/** A block without level counts as comfort, like the integration reads it. */
function levelOf(data: Record<string, unknown> | undefined): Level {
  return data?.level === "night" ? "night" : "comfort";
}

export function weekOf(item: ScheduleItem): Week {
  return WEEKDAYS.map((weekday) =>
    sorted(
      (item[weekday] ?? []).map((block) => ({
        from: minutes(block.from),
        to: minutes(block.to),
        level: levelOf(block.data),
        data: block.data ?? {},
      })),
    ),
  );
}

export function scheduleWeekOf(week: Week): ScheduleWeek {
  const result = {} as ScheduleWeek;
  WEEKDAYS.forEach((weekday, day) => {
    result[weekday] = week[day].map(
      (block): ScheduleBlock => ({
        from: `${clock(block.from)}:00`,
        to: `${clock(block.to)}:00`,
        data: { ...block.data, level: block.level },
      }),
    );
  });
  return result;
}

function sorted(blocks: Block[]): Block[] {
  return [...blocks].sort((a, b) => a.from - b.from);
}

function block(from: number, to: number, level: Level = "comfort"): Block {
  return { from, to, level, data: {} };
}

export function emptyWeek(): Week {
  return ALL_DAYS.map(() => []);
}

/** Mon–Fri 06–08 and 16–21 comfort, Sat–Sun 07:30–21 comfort, night from 21 until then. */
export function standardWeek(): Week {
  const workday = [block(0, 6 * 60, "night"), block(6 * 60, 8 * 60), block(16 * 60, 21 * 60), block(21 * 60, DAY, "night")];
  const weekend = [block(0, 7 * 60 + 30, "night"), block(7 * 60 + 30, 21 * 60), block(21 * 60, DAY, "night")];
  return ALL_DAYS.map((day) => (WEEKEND.includes(day) ? weekend : workday).map((b) => ({ ...b, data: {} })));
}

export function copyWeek(week: Week): Week {
  return week.map((blocks) => blocks.map((b) => ({ ...b, data: { ...b.data } })));
}

/** Whether `from`–`to` overlaps a block of the day other than `ignore`. */
export function overlaps(blocks: Block[], from: number, to: number, ignore = -1): boolean {
  return blocks.some((b, index) => index !== ignore && from < b.to && to > b.from);
}

/** Where block `index` may move: from the end of the previous to the start of the next block. */
export function room(blocks: Block[], index: number): { lo: number; hi: number } {
  return {
    lo: index > 0 ? blocks[index - 1].to : 0,
    hi: index < blocks.length - 1 ? blocks[index + 1].from : DAY,
  };
}

/** A free range of up to `length` minutes starting at `preferred` or the next free moment. */
export function freeRange(blocks: Block[], preferred: number, length: number): { from: number; to: number } | null {
  for (const candidate of [preferred, ...blocks.map((b) => b.to), 0]) {
    const from = Math.max(0, Math.min(DAY - STEP, candidate));
    if (blocks.some((b) => from >= b.from && from < b.to)) {
      continue;
    }
    const next = Math.min(DAY, ...blocks.filter((b) => b.from > from).map((b) => b.from));
    if (next - from >= STEP) {
      return { from, to: Math.min(from + length, next) };
    }
  }
  return null;
}

/** The week with the blocks of `day` replaced; the day stays sorted. */
export function withDay(week: Week, day: number, blocks: Block[]): Week {
  return week.map((current, index) => (index === day ? sorted(blocks) : current));
}

/** Copy block `index` of `day` to `targets`; days where it would overlap are skipped. */
export function copyBlock(week: Week, day: number, index: number, targets: number[]): { week: Week; skipped: number[] } {
  const source = week[day][index];
  const skipped: number[] = [];
  let result = week;
  for (const target of targets) {
    if (target === day) {
      continue;
    }
    if (overlaps(result[target], source.from, source.to)) {
      skipped.push(target);
      continue;
    }
    result = withDay(result, target, [...result[target], { ...source, data: { ...source.data } }]);
  }
  return { week: result, skipped };
}

/** Copy all blocks of `day` to `targets`, replacing their blocks. */
export function copyDay(week: Week, day: number, targets: number[]): Week {
  return week.map((blocks, index) =>
    targets.includes(index) && index !== day ? week[day].map((b) => ({ ...b, data: { ...b.data } })) : blocks,
  );
}

/**
 * The counterpart across midnight of block `index` of `day`: a block until
 * 24:00 goes on in a block from 00:00 the next day, a block from 00:00 began in
 * one until 24:00 the day before.
 */
export function acrossMidnight(
  week: Week,
  day: number,
  index: number,
): { continuesUntil?: { day: number; to: number }; since?: { day: number; from: number } } {
  const current = week[day][index];
  const result: { continuesUntil?: { day: number; to: number }; since?: { day: number; from: number } } = {};
  if (current.to === DAY) {
    const next = (day + 1) % 7;
    const counterpart = week[next].find((b) => b.from === 0);
    if (counterpart) {
      result.continuesUntil = { day: next, to: counterpart.to };
    }
  }
  if (current.from === 0) {
    const previous = (day + 6) % 7;
    const counterpart = week[previous].find((b) => b.to === DAY);
    if (counterpart) {
      result.since = { day: previous, from: counterpart.from };
    }
  }
  return result;
}

/** Today as a day of the week, Monday 0, on the clock of the phone. */
export function today(): number {
  return (new Date().getDay() + 6) % 7;
}

/** Minutes since midnight now, on the clock of the phone. */
export function nowMinutes(): number {
  const now = new Date();
  return now.getHours() * 60 + now.getMinutes();
}
