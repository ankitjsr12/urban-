type WsEvent = { channel: string; [key: string]: unknown };
type Handler = (event: WsEvent) => void;

const WS_BASE = import.meta.env.VITE_WS_URL || 'wss://urbansense-api.onrender.com';
const VALID_CHANNELS = ['buses', 'incidents', 'detections', 'traffic'] as const;
type Channel = typeof VALID_CHANNELS[number];

class WebSocketManager {
  private sockets: Map<Channel, WebSocket> = new Map();
  private handlers: Map<Channel, Set<Handler>> = new Map();
  private reconnectTimers: Map<Channel, ReturnType<typeof setTimeout>> = new Map();

  connect(channel: Channel): void {
    if (this.sockets.get(channel)?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE}/live/${channel}`);

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as WsEvent;
        this.handlers.get(channel)?.forEach((h) => h({ ...data, channel }));
      } catch {
        // ignore malformed frames
      }
    };

    ws.onclose = () => {
      this.sockets.delete(channel);
      // Exponential back-off reconnect
      const timer = setTimeout(() => this.connect(channel), 3000);
      this.reconnectTimers.set(channel, timer);
    };

    ws.onerror = () => ws.close();

    this.sockets.set(channel, ws);
  }

  disconnect(channel: Channel): void {
    const timer = this.reconnectTimers.get(channel);
    if (timer) clearTimeout(timer);
    this.reconnectTimers.delete(channel);
    this.sockets.get(channel)?.close();
    this.sockets.delete(channel);
  }

  subscribe(channel: Channel, handler: Handler): () => void {
    if (!this.handlers.has(channel)) this.handlers.set(channel, new Set());
    this.handlers.get(channel)!.add(handler);
    this.connect(channel);
    return () => {
      this.handlers.get(channel)?.delete(handler);
      if (this.handlers.get(channel)?.size === 0) this.disconnect(channel);
    };
  }

  isConnected(channel: Channel): boolean {
    return this.sockets.get(channel)?.readyState === WebSocket.OPEN;
  }
}

export const wsManager = new WebSocketManager();
export type { Channel, Handler as WsHandler };
