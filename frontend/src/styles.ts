// Styles shared by all tabs. Colours come from the Home Assistant theme.

import { css } from "lit";

export const sharedStyles = css`
  :host {
    --cc-auto: var(--state-climate-auto-color, #2e7d32);
    --cc-heat: var(--state-climate-heat-color, #e65100);
    --cc-off: var(--state-climate-off-color, #757575);
    --cc-frost: #4fc3f7;
    --cc-night: #5c6bc0;
    --cc-muted: var(--secondary-text-color, #6f6f6f);
    --cc-divider: var(--divider-color, rgba(0, 0, 0, 0.12));
    --cc-card: var(--card-background-color, #fff);
    --cc-primary: var(--primary-color, #03a9f4);
  }
  .card {
    background: var(--cc-card);
    border: 1px solid var(--cc-divider);
    border-radius: var(--ha-card-border-radius, 12px);
    margin-bottom: 12px;
  }
  .pad {
    padding: 14px;
  }
  .muted {
    color: var(--cc-muted);
  }
  .small {
    font-size: 13px;
  }
  h2.section {
    font-size: 15px;
    font-weight: 600;
    color: var(--cc-muted);
    margin: 20px 2px 8px;
  }
  .chips {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding-bottom: 6px;
    margin-bottom: 6px;
  }
  .chip {
    border: 1px solid var(--cc-divider);
    border-radius: 16px;
    padding: 6px 12px;
    background: var(--cc-card);
    color: var(--primary-text-color);
    font: inherit;
    font-size: 14px;
    white-space: nowrap;
    cursor: pointer;
  }
  .chip.selected {
    background: var(--cc-primary);
    border-color: transparent;
    color: var(--text-primary-color, #fff);
  }
`;
