import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, CheckCheck } from 'lucide-react';
import clsx from 'clsx';
import { notificationApi } from '../api/endpoints';
import { Avatar, EmptyState, LoadMore, PageLoader } from '../components/ui';
import { useCursorList } from '../hooks/useCursorList';
import { timeAgo } from '../lib/format';

function linkOf(n) {
  if (n.entity_type === 'POST') return `/posts/${n.entity_id}`;
  if (n.entity_type === 'USER') return n.verb === 'FRIEND_REQUEST' ? '/friends' : `/u/${n.entity_id}`;
  if (n.entity_type === 'GROUP') return `/groups/${n.entity_id}`;
  return null;
}

/** UC-25, UC-26: danh sách thông báo realtime, đánh dấu đã đọc từng cái / tất cả. */
export default function NotificationsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const list = useCursorList(['notifications', 'list'], notificationApi.list);
  const refresh = (d) => {
    qc.setQueryData(['notifications', 'unread'], d);
    qc.invalidateQueries({ queryKey: ['notifications', 'list'] });
  };
  const readOne = useMutation({ mutationFn: notificationApi.read, onSuccess: refresh });
  const readAll = useMutation({ mutationFn: notificationApi.readAll, onSuccess: refresh });
  const unread = list.firstPage?.unread_count || 0;

  return (
    <div className="mx-auto max-w-[640px]">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Thông báo</h1>
        {unread > 0 && (
          <button className="btn-ghost" onClick={() => readAll.mutate()}>
            <CheckCheck className="h-4 w-4" /> Đánh dấu tất cả đã đọc
          </button>
        )}
      </div>
      {list.isLoading && <PageLoader />}
      {list.isSuccess && list.items.length === 0 && (
        <EmptyState icon={Bell} title="Bạn chưa có thông báo nào" />
      )}
      {list.items.length > 0 && (
        <ul className="card divide-y divide-line overflow-hidden">
          {list.items.map((n) => (
            <li key={n.id}>
              <button
                className={clsx(
                  'flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-paper',
                  !n.is_read && 'bg-amber-50/60',
                )}
                onClick={() => {
                  if (!n.is_read) readOne.mutate(n.id);
                  const to = linkOf(n);
                  if (to) navigate(to);
                }}
              >
                {n.actor ? <Avatar user={n.actor} size={44} /> : <Bell className="m-2.5 h-6 w-6 text-ink" />}
                <span className="min-w-0 flex-1">
                  <span className="block text-sm">{n.content}</span>
                  <span className={clsx('text-xs', n.is_read ? 'text-muted' : 'font-semibold text-ink')}>
                    {timeAgo(n.created_at)}
                  </span>
                </span>
                {!n.is_read && (
                  <span className="mt-2 h-2.5 w-2.5 rounded-full bg-amber" aria-label="Chưa đọc" />
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
      <LoadMore query={list} />
    </div>
  );
}
