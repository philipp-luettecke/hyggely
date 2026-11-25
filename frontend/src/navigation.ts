// Moving between the tabs of the panel, e.g. from the overview to a room page.

export type Tab = "overview" | "rooms" | "house";

export interface NavigateDetail {
  tab: Tab;
  roomId?: string;
}

export const NAVIGATE_EVENT = "cc-navigate";

/** Ask the panel to show `tab`; for the rooms tab optionally a room page. */
export function navigate(from: HTMLElement, tab: Tab, roomId?: string): void {
  from.dispatchEvent(
    new CustomEvent<NavigateDetail>(NAVIGATE_EVENT, {
      detail: { tab, roomId },
      bubbles: true,
      composed: true,
    }),
  );
}
