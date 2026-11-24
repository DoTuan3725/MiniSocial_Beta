import { create } from 'zustand';

let seq = 0;
export const useToast = create((set, get) => ({
  items: [],
  push: (text, tone = 'info') => {
    const id = ++seq;
    set({ items: [...get().items, { id, text, tone }] });
    setTimeout(() => set({ items: get().items.filter((t) => t.id !== id) }), 4000);
  },
  dismiss: (id) => set({ items: get().items.filter((t) => t.id !== id) }),
}));

export const toast = {
  info: (t) => useToast.getState().push(t, 'info'),
  success: (t) => useToast.getState().push(t, 'success'),
  error: (t) => useToast.getState().push(t, 'error'),
};
