// −/+ stepper for temperatures and the lead time (ticket 19), and the delayed
// saving of what was stepped.

import { css, html, type TemplateResult } from "lit";

export const MIN_TEMPERATURE = 5;
export const MAX_TEMPERATURE = 25;
export const LEAD_TIME_STEP_MINUTES = 15;
export const MAX_LEAD_TIME_MINUTES = 180;
/** Quiet time after the last tap before the changes are sent. */
export const SAVE_DELAY_MS = 1000;

/** One step in whole degrees; a half value moves to the next whole degree. */
export function stepTemperature(value: number, direction: 1 | -1): number {
  const next = direction > 0 ? Math.floor(value) + 1 : Math.ceil(value) - 1;
  return Math.min(MAX_TEMPERATURE, Math.max(MIN_TEMPERATURE, next));
}

/** One step of 15 minutes; a value off the steps moves to the next step. */
export function stepLeadTime(minutes: number, direction: 1 | -1): number {
  const steps = minutes / LEAD_TIME_STEP_MINUTES;
  const next = (direction > 0 ? Math.floor(steps) + 1 : Math.ceil(steps) - 1) * LEAD_TIME_STEP_MINUTES;
  return Math.min(MAX_LEAD_TIME_MINUTES, Math.max(0, next));
}

export function stepper(options: {
  label: TemplateResult | string;
  value: string;
  less: string;
  more: string;
  canDown: boolean;
  canUp: boolean;
  onStep: (direction: 1 | -1) => void;
}): TemplateResult {
  return html`<div class="row">
    <span class="row-name">${options.label}</span>
    <span class="stepper">
      <button aria-label=${options.less} ?disabled=${!options.canDown} @click=${() => options.onStep(-1)}>−</button>
      <span class="value">${options.value}</span>
      <button aria-label=${options.more} ?disabled=${!options.canUp} @click=${() => options.onStep(1)}>+</button>
    </span>
  </div>`;
}

export const stepperStyles = css`
  .row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    padding: 5px 0;
  }
  .row-name {
    display: flex;
    align-items: center;
  }
  .stepper {
    display: inline-flex;
    align-items: center;
    border: 1px solid var(--cc-divider);
    border-radius: 10px;
    overflow: hidden;
  }
  .stepper button {
    width: 44px;
    height: 40px;
    border: 0;
    background: transparent;
    color: var(--cc-primary);
    font: inherit;
    font-size: 20px;
    line-height: 1;
    cursor: pointer;
  }
  .stepper button:disabled {
    color: var(--cc-muted);
    opacity: 0.35;
    cursor: default;
  }
  .stepper .value {
    min-width: 84px;
    text-align: center;
    font-variant-numeric: tabular-nums;
  }
  .hint {
    margin: 8px 0 0;
    color: var(--warning-color, #e65100);
  }
  .error {
    margin: 8px 0 0;
    color: var(--error-color, #d32f2f);
  }
`;

/**
 * Collects stepped changes and sends them once the taps pause, or at once
 * when the panel is left or goes to the background.
 */
export class DelayedSave<T extends object> {
  private _changes: Partial<T> = {};
  private _timer?: number;

  constructor(private readonly _send: (changes: Partial<T>) => void) {}

  get changes(): Partial<T> {
    return this._changes;
  }

  change(changes: Partial<T>): void {
    this._changes = { ...this._changes, ...changes };
    window.clearTimeout(this._timer);
    this._timer = window.setTimeout(this.flush, SAVE_DELAY_MS);
  }

  flush = (): void => {
    window.clearTimeout(this._timer);
    this._timer = undefined;
    const changes = this._changes;
    if (Object.keys(changes).length === 0) {
      return;
    }
    this._changes = {};
    this._send(changes);
  };

  connect(): void {
    document.addEventListener("visibilitychange", this._flushWhenHidden);
    window.addEventListener("pagehide", this.flush);
  }

  disconnect(): void {
    document.removeEventListener("visibilitychange", this._flushWhenHidden);
    window.removeEventListener("pagehide", this.flush);
    this.flush();
  }

  private _flushWhenHidden = (): void => {
    if (document.visibilityState === "hidden") {
      this.flush();
    }
  };
}
