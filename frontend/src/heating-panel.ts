// Heating panel: the sidebar entry "Heizung". A toolbar, the tabs overview,
// rooms and house, and the subscription of the room overview they share.
// The panel holds no heating logic; it only talks to the panel API.

import { LitElement, css, html, nothing, type PropertyDeclarations, type PropertyValues } from "lit";
import { subscribeRooms, type RoomOverview } from "./api/rooms";
import "./house/house-tab";
import { errorMessage, format, localize } from "./i18n";
import { NAVIGATE_EVENT, type NavigateDetail, type Tab } from "./navigation";
import "./overview/overview-tab";
import "./rooms/rooms-tab";
import { sharedStyles } from "./styles";
import type { HomeAssistant, Unsubscribe } from "./types";

const TABS: Tab[] = ["overview", "rooms", "house"];
const MENU_ICON = "M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z";

const TEXTS = {
  de: {
    title: "Heizung",
    overview: "Übersicht",
    rooms: "Räume",
    house: "Haus",
    menu: "Seitenleiste",
    loading: "Lade Räume …",
    failed: "Die Heizungssteuerung antwortet nicht: {error}",
  },
  en: {
    title: "Heating",
    overview: "Overview",
    rooms: "Rooms",
    house: "House",
    menu: "Sidebar",
    loading: "Loading rooms …",
    failed: "The heating control does not answer: {error}",
  },
};

type Text = (typeof TEXTS)["de"];

export class HeatingPanel extends LitElement {
  static override properties: PropertyDeclarations = {
    hass: { attribute: false },
    narrow: { type: Boolean },
    _tab: { state: true },
    _roomId: { state: true },
    _rooms: { state: true },
    _error: { state: true },
  };

  hass?: HomeAssistant;
  narrow = false;
  private _tab: Tab = "overview";
  private _roomId?: string;
  private _rooms?: RoomOverview[];
  private _error?: string;
  private _unsubscribe?: Promise<Unsubscribe>;

  constructor() {
    super();
    this.addEventListener(NAVIGATE_EVENT, (event) => {
      const { tab, roomId } = (event as CustomEvent<NavigateDetail>).detail;
      this._tab = tab;
      if (roomId !== undefined) {
        this._roomId = roomId;
      }
    });
  }

  override connectedCallback(): void {
    super.connectedCallback();
    this._subscribe();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    const unsubscribe = this._unsubscribe;
    this._unsubscribe = undefined;
    unsubscribe?.then((stop) => stop()).catch(() => undefined);
  }

  protected override updated(changed: PropertyValues): void {
    if (changed.has("hass")) {
      this._subscribe();
    }
  }

  private _subscribe(): void {
    if (!this.hass || !this.isConnected || this._unsubscribe) {
      return;
    }
    this._unsubscribe = subscribeRooms(this.hass, (rooms) => {
      this._rooms = rooms;
      this._error = undefined;
    });
    this._unsubscribe.catch((error: unknown) => {
      this._error = format(localize(this.hass, TEXTS).failed, { error: errorMessage(error) });
    });
  }

  protected override render() {
    const t = localize(this.hass, TEXTS);
    return html`
      <div class="sticky">
        <header class="toolbar">
          ${this.narrow
            ? html`<button class="menu" aria-label=${t.menu} @click=${this._toggleMenu}>
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d=${MENU_ICON}></path></svg>
              </button>`
            : nothing}
          <div class="title">${t.title}</div>
        </header>
        <nav class="tabs" role="tablist">
          ${TABS.map(
            (tab) => html`<button
              class="tab ${tab === this._tab ? "selected" : ""}"
              role="tab"
              aria-selected=${tab === this._tab}
              @click=${() => (this._tab = tab)}
            >
              ${t[tab]}
            </button>`,
          )}
        </nav>
      </div>
      <main>${this._content(t)}</main>
    `;
  }

  private _content(t: Text) {
    if (this._tab === "house") {
      return html`<cc-house-tab .hass=${this.hass}></cc-house-tab>`;
    }
    if (this._error) {
      return html`<p class="error">${this._error}</p>`;
    }
    if (!this._rooms) {
      return html`<p class="muted">${t.loading}</p>`;
    }
    if (this._tab === "rooms") {
      return html`<cc-rooms-tab .hass=${this.hass} .rooms=${this._rooms} .roomId=${this._roomId}></cc-rooms-tab>`;
    }
    return html`<cc-overview-tab .hass=${this.hass} .rooms=${this._rooms}></cc-overview-tab>`;
  }

  private _toggleMenu(): void {
    this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
  }

  static override styles = [
    sharedStyles,
    css`
      :host {
        display: block;
        min-height: 100%;
        background: var(--primary-background-color, #fafafa);
        color: var(--primary-text-color, #212121);
        font-family: var(--ha-font-family-body, Roboto, system-ui, -apple-system, "Segoe UI", sans-serif);
        font-size: 15px;
        -webkit-tap-highlight-color: transparent;
      }
      .sticky {
        position: sticky;
        top: 0;
        z-index: 5;
      }
      .toolbar {
        display: flex;
        align-items: center;
        gap: 8px;
        height: var(--header-height, 56px);
        padding: 0 12px;
        background: var(--app-header-background-color, var(--cc-primary));
        color: var(--app-header-text-color, #fff);
      }
      .menu {
        display: flex;
        border: 0;
        background: transparent;
        color: inherit;
        padding: 8px;
        border-radius: 50%;
        cursor: pointer;
      }
      .menu svg {
        width: 24px;
        height: 24px;
        fill: currentColor;
      }
      .title {
        font-size: 20px;
        margin-left: 4px;
      }
      .tabs {
        display: flex;
        background: var(--cc-card);
        border-bottom: 1px solid var(--cc-divider);
      }
      .tab {
        flex: 1;
        padding: 12px 8px;
        border: 0;
        border-bottom: 2px solid transparent;
        background: transparent;
        color: var(--cc-muted);
        font: inherit;
        font-weight: 500;
        cursor: pointer;
      }
      .tab.selected {
        color: var(--cc-primary);
        border-bottom-color: var(--cc-primary);
      }
      main {
        max-width: 960px;
        margin: 0 auto;
        padding: 16px 16px calc(96px + env(safe-area-inset-bottom));
      }
      .error {
        color: var(--error-color, #d32f2f);
      }
    `,
  ];
}

if (!customElements.get("hyggely-panel")) {
  customElements.define("hyggely-panel", HeatingPanel);
}
