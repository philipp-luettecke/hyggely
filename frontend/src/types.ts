// The parts of the `hass` object of the Home Assistant frontend the panel uses.

export type Unsubscribe = () => Promise<void>;

export interface HassConnection {
  subscribeMessage<T>(
    callback: (message: T) => void,
    message: Record<string, unknown>,
  ): Promise<Unsubscribe>;
}

export interface HomeAssistant {
  language: string;
  locale?: { language: string };
  connection: HassConnection;
  callWS<T>(message: Record<string, unknown>): Promise<T>;
}
