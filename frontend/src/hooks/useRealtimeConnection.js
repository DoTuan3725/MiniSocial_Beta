import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../api/endpoints';
import { wsBaseUrl } from '../lib/config';
import { useAuth } from '../store/auth';
import { useRealtime } from '../store/realtime';
import { toast } from '../store/toast';

/**
 * Một kết nối WebSocket cho cả ứng dụng: tin nhắn, typing, đã xem, online, thông báo.
 * Tự kết nối lại (backoff tối đa 15s) và ping 25s/lần để giữ trạng thái online.
 */
export function useRealtimeConnection() {
  const token = useAuth((s) => s.accessToken);
  const myId = useAuth((s) => s.user?.id);
  const qc = useQueryClient();
  const retry = useRef(0);

  useEffect(() => {
    if (!token) return undefined;
    let ws;
    let pingTimer;
    let reconnectTimer;
    let closedByUs = false;
    const store = useRealtime.getState();

    const handle = ({ type, data }) => {
      if (type === 'message.new') {
        qc.setQueryData(['messages', data.conversation_id], (old) => {
          if (!old) return old;
          const pages = [...old.pages];
          const first = pages[0];
          const rest = first.results.filter((m) => !(data.client_id && m.client_id === data.client_id));
          if (rest.some((m) => m.id === data.id)) return old;
          pages[0] = { ...first, results: [data, ...rest] };
          return { ...old, pages };
        });
        qc.invalidateQueries({ queryKey: ['conversations'] });
        const viewing = window.location.pathname === `/chat/${data.conversation_id}`;
        if (data.sender_id !== myId && !viewing) {
          toast.info(`${data.sender?.full_name || 'Tin nhắn mới'}: ${data.content || 'đã gửi một tệp'}`);
        }
        store.setTyping(data.conversation_id, data.sender_id, '', false);
      } else if (type === 'message.read') {
        qc.invalidateQueries({ queryKey: ['conversation', data.conversation_id] });
        qc.invalidateQueries({ queryKey: ['conversations'] });
      } else if (type === 'typing') {
        store.setTyping(data.conversation_id, data.user_id, data.full_name, data.is_typing);
      } else if (type === 'presence') {
        store.setPresence(data.user_id, data.is_online);
      } else if (type === 'notification.new') {
        qc.setQueryData(['notifications', 'unread'], { unread_count: data.unread_count });
        qc.invalidateQueries({ queryKey: ['notifications', 'list'] });
        if (data.verb?.startsWith('FRIEND')) qc.invalidateQueries({ queryKey: ['friend-requests'] });
        toast.info(data.content);
      } else if (type === 'conversation.new') {
        qc.invalidateQueries({ queryKey: ['conversations'] });
      } else if (type === 'error') {
        toast.error(data.message);
      }
    };

    const connect = () => {
      ws = new WebSocket(`${wsBaseUrl()}/ws/chat/?token=${encodeURIComponent(token)}`);
      store.setSocket(ws);
      ws.onopen = () => {
        retry.current = 0;
        store.setConnected(true);
        chatApi
          .presence()
          .then((d) => useRealtime.getState().setOnline(d.online))
          .catch(() => {});
        pingTimer = setInterval(
          () => ws.readyState === 1 && ws.send(JSON.stringify({ type: 'ping' })),
          25000,
        );
      };
      ws.onmessage = (e) => {
        try {
          handle(JSON.parse(e.data));
        } catch {
          /* bỏ qua gói tin không hợp lệ */
        }
      };
      ws.onclose = () => {
        clearInterval(pingTimer);
        store.setConnected(false);
        if (closedByUs) return;
        const delay = Math.min(15000, 1000 * 2 ** retry.current++);
        reconnectTimer = setTimeout(connect, delay);
      };
    };

    connect();
    return () => {
      closedByUs = true;
      clearInterval(pingTimer);
      clearTimeout(reconnectTimer);
      ws?.close();
      store.setSocket(null);
    };
  }, [token, qc, myId]);
}
