import { create } from 'zustand';

export const useRealtime = create((set, get) => ({
  connected: false,
  online: new Set(),
  typing: {}, // conversationId -> { userId: { name, until } }
  socket: null,
  setSocket: (socket) => set({ socket }),
  setConnected: (connected) => set({ connected }),
  setOnline: (ids) => set({ online: new Set(ids) }),
  setPresence: (userId, isOnline) => {
    const online = new Set(get().online);
    if (isOnline) online.add(userId);
    else online.delete(userId);
    set({ online });
  },
  setTyping: (conversationId, userId, name, isTyping) => {
    const typing = { ...get().typing };
    const conv = { ...(typing[conversationId] || {}) };
    if (isTyping) conv[userId] = { name, until: Date.now() + 5000 };
    else delete conv[userId];
    typing[conversationId] = conv;
    set({ typing });
  },
  send: (payload) => {
    const ws = get().socket;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
      return true;
    }
    return false;
  },
}));
