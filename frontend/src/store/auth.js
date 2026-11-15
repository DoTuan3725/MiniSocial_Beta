import { create } from 'zustand';

/** Access token chỉ nằm trong RAM (không localStorage) để chống XSS đọc trộm. */
export const useAuth = create((set) => ({
  accessToken: null,
  user: null,
  ready: false,
  setSession: (accessToken, user) => set((s) => ({ accessToken, user: user ?? s.user, ready: true })),
  setUser: (user) => set({ user }),
  clear: () => set({ accessToken: null, user: null, ready: true }),
  markReady: () => set({ ready: true }),
}));
