import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { X, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { useToast } from '../store/toast';
import { useRealtime } from '../store/realtime';

export function Logo({ className }) {
  return (
    <Link to="/" className={clsx('flex items-center gap-2 font-bold text-ink', className)}>
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden="true">
        <rect width="32" height="32" rx="7" fill="#1F3A5F" />
        <path
          d="M8 22V10l8 7 8-7v12"
          fill="none"
          stroke="#E8A33D"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="text-lg tracking-tight">MiniSocial</span>
    </Link>
  );
}

/** Ảnh vừa tải lên có thể chưa sẵn sàng (Celery đang nén WebP) -> thử tải lại vài lần. */
export function RetryImage({ src, alt = '', className, ...rest }) {
  const [attempt, setAttempt] = useState(0);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    setAttempt(0);
    setFailed(false);
  }, [src]);
  if (!src) return null;
  const url = attempt ? `${src}${src.includes('?') ? '&' : '?'}r=${attempt}` : src;
  if (failed) return <div className={clsx('bg-ink-50', className)} aria-label="Ảnh đang được xử lý" />;
  return (
    <img
      src={url}
      alt={alt}
      loading="lazy"
      className={className}
      onError={() => {
        if (attempt < 6) setTimeout(() => setAttempt((a) => a + 1), 1200);
        else setFailed(true);
      }}
      {...rest}
    />
  );
}

export function Avatar({ user, size = 40, showOnline = false, className }) {
  const online = useRealtime((s) => (user?.id ? s.online.has(user.id) : false));
  const initials = (user?.full_name || '?')
    .split(' ')
    .filter(Boolean)
    .slice(-2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();
  return (
    <span className={clsx('relative inline-flex shrink-0', className)} style={{ width: size, height: size }}>
      {user?.avatar_url ? (
        <RetryImage
          src={user.avatar_url}
          alt={user.full_name}
          className="h-full w-full rounded-full object-cover"
        />
      ) : (
        <span
          className="flex h-full w-full items-center justify-center rounded-full bg-ink-100 font-semibold text-ink"
          style={{ fontSize: size * 0.38 }}
        >
          {initials}
        </span>
      )}
      {showOnline && online && (
        <span
          className="absolute bottom-0 right-0 rounded-full border-2 border-white bg-success"
          style={{ width: size * 0.3, height: size * 0.3 }}
          title="Đang hoạt động"
        />
      )}
    </span>
  );
}

export function Spinner({ className }) {
  return <Loader2 className={clsx('h-5 w-5 animate-spin text-ink', className)} aria-label="Đang tải" />;
}

export function PageLoader() {
  return (
    <div className="flex justify-center py-16">
      <Spinner className="h-7 w-7" />
    </div>
  );
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="card flex flex-col items-center px-6 py-12 text-center">
      {Icon && <Icon className="mb-3 h-10 w-10 text-ink/40" />}
      <p className="font-semibold text-text">{title}</p>
      {children && <p className="mt-1 max-w-sm text-sm text-muted">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Modal({ open, onClose, title, children, wide }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink-900/40 p-0 sm:items-center sm:p-4">
      <div className="absolute inset-0" onClick={onClose} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={clsx(
          'relative max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-white shadow-xl sm:rounded-2xl',
          wide ? 'sm:max-w-2xl' : 'sm:max-w-md',
        )}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-line bg-white px-5 py-3.5">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} className="rounded-full p-1.5 hover:bg-ink-50" aria-label="Đóng">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

export function Toaster() {
  const { items, dismiss } = useToast();
  return (
    <div className="fixed bottom-20 right-4 z-[60] flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2 lg:bottom-4">
      {items.map((t) => (
        <div
          key={t.id}
          role="status"
          className={clsx(
            'flex items-start gap-3 rounded-xl px-4 py-3 text-sm shadow-lg',
            t.tone === 'error' && 'bg-danger text-white',
            t.tone === 'success' && 'bg-success text-white',
            t.tone === 'info' && 'bg-ink text-white',
          )}
        >
          <span className="flex-1">{t.text}</span>
          <button onClick={() => dismiss(t.id)} aria-label="Đóng thông báo">
            <X className="h-4 w-4 opacity-70" />
          </button>
        </div>
      ))}
    </div>
  );
}

export function LoadMore({ query }) {
  if (!query.hasNextPage) return null;
  return (
    <div className="flex justify-center py-4">
      <button className="btn-ghost" onClick={() => query.fetchNextPage()} disabled={query.isFetchingNextPage}>
        {query.isFetchingNextPage ? <Spinner className="h-4 w-4" /> : 'Xem thêm'}
      </button>
    </div>
  );
}

export function UserLink({ user, className }) {
  if (!user) return null;
  return (
    <Link to={`/u/${user.id}`} className={clsx('font-semibold hover:underline', className)}>
      {user.full_name}
    </Link>
  );
}

export function Tabs({ tabs, value, onChange }) {
  return (
    <div className="flex gap-1 overflow-x-auto border-b border-line" role="tablist">
      {tabs.map((t) => (
        <button
          key={t.value}
          role="tab"
          aria-selected={value === t.value}
          onClick={() => onChange(t.value)}
          className={clsx(
            '-mb-px whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium',
            value === t.value ? 'border-amber text-ink' : 'border-transparent text-muted hover:text-text',
          )}
        >
          {t.label}
          {t.count ? (
            <span className="ml-1.5 rounded-full bg-amber px-1.5 text-xs text-ink-900">{t.count}</span>
          ) : null}
        </button>
      ))}
    </div>
  );
}
