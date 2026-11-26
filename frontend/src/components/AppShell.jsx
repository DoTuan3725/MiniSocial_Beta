import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Home,
  Users,
  UsersRound,
  MessageCircle,
  Bell,
  Shield,
  Search,
  LogOut,
  Settings,
  UserRound,
  WifiOff,
} from 'lucide-react';
import clsx from 'clsx';
import { authApi, chatApi, notificationApi, userApi } from '../api/endpoints';
import { useRealtimeConnection } from '../hooks/useRealtimeConnection';
import { useAuth } from '../store/auth';
import { useRealtime } from '../store/realtime';
import { Avatar, Logo } from './ui';

function useBadges() {
  const unreadNoti = useQuery({ queryKey: ['notifications', 'unread'], queryFn: notificationApi.unread });
  const unreadChat = useQuery({ queryKey: ['conversations', 'unread'], queryFn: chatApi.unread });
  const requests = useQuery({
    queryKey: ['friend-requests', 'received'],
    queryFn: () => userApi.requests('received'),
  });
  return {
    notifications: unreadNoti.data?.unread_count || 0,
    chat: unreadChat.data?.unread_conversations || 0,
    friends: requests.data?.length || 0,
  };
}

function Badge({ n }) {
  if (!n) return null;
  return (
    <span className="ml-auto min-w-5 rounded-full bg-amber px-1.5 text-center text-xs font-bold leading-5 text-ink-900">
      {n > 99 ? '99+' : n}
    </span>
  );
}

function navItems(user, badges) {
  const items = [
    { to: '/', label: 'Bảng tin', icon: Home, end: true },
    { to: '/friends', label: 'Bạn bè', icon: Users, badge: badges.friends },
    { to: '/groups', label: 'Nhóm', icon: UsersRound },
    { to: '/chat', label: 'Tin nhắn', icon: MessageCircle, badge: badges.chat },
    { to: '/notifications', label: 'Thông báo', icon: Bell, badge: badges.notifications },
  ];
  if (user?.role === 'ADMIN') items.push({ to: '/admin', label: 'Quản trị', icon: Shield });
  return items;
}

function TopBar() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const user = useAuth((s) => s.user);
  const connected = useRealtime((s) => s.connected);
  const [q, setQ] = useState('');
  const [menu, setMenu] = useState(false);
  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      useAuth.getState().clear();
      qc.clear();
      navigate('/login');
    }
  };
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-3 sm:px-5">
        <Logo />
        <form
          className="relative ml-2 hidden max-w-xs flex-1 sm:block"
          onSubmit={(e) => {
            e.preventDefault();
            if (q.trim().length >= 2) navigate(`/search?q=${encodeURIComponent(q.trim())}`);
          }}
        >
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Tìm người dùng (có dấu hoặc không)"
            className="w-full rounded-full border-0 bg-paper py-2 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-ink/20"
            aria-label="Tìm kiếm người dùng"
          />
        </form>
        <div className="ml-auto flex items-center gap-2">
          {!connected && (
            <span
              className="hidden items-center gap-1 text-xs text-muted sm:flex"
              title="Mất kết nối realtime, đang thử lại"
            >
              <WifiOff className="h-4 w-4" /> Đang kết nối lại
            </span>
          )}
          <Link to="/search" className="rounded-full p-2 hover:bg-paper sm:hidden" aria-label="Tìm kiếm">
            <Search className="h-5 w-5" />
          </Link>
          <div className="relative">
            <button
              onClick={() => setMenu(!menu)}
              className="flex items-center gap-2 rounded-full p-0.5 hover:bg-paper"
              aria-label="Tài khoản"
            >
              <Avatar user={user} size={34} />
            </button>
            {menu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenu(false)} />
                <div className="absolute right-0 z-20 mt-2 w-56 overflow-hidden rounded-xl border border-line bg-white py-1 shadow-lg">
                  <div className="border-b border-line px-3 py-2">
                    <p className="truncate text-sm font-semibold">{user?.full_name}</p>
                    <p className="truncate text-xs text-muted">{user?.email}</p>
                  </div>
                  {[
                    { to: `/u/${user?.id}`, label: 'Trang cá nhân', icon: UserRound },
                    { to: '/settings', label: 'Cài đặt', icon: Settings },
                  ].map((i) => (
                    <Link
                      key={i.to}
                      to={i.to}
                      onClick={() => setMenu(false)}
                      className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-paper"
                    >
                      <i.icon className="h-4 w-4" /> {i.label}
                    </Link>
                  ))}
                  <button
                    onClick={logout}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-danger hover:bg-paper"
                  >
                    <LogOut className="h-4 w-4" /> Đăng xuất
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

function OnlineFriends() {
  const online = useRealtime((s) => s.online);
  const navigate = useNavigate();
  const friends = useQuery({ queryKey: ['friends', 'me'], queryFn: () => userApi.friends() });
  const list = (friends.data || [])
    .slice()
    .sort((a, b) => Number(online.has(b.id)) - Number(online.has(a.id)));
  const openChat = async (id) => {
    const conv = await chatApi.direct(id);
    navigate(`/chat/${conv.id}`);
  };
  return (
    <section>
      <h2 className="mb-2 px-2 text-sm font-semibold text-muted">Người liên hệ</h2>
      {list.length === 0 && <p className="px-2 text-sm text-muted">Chưa có bạn bè.</p>}
      <ul className="space-y-0.5">
        {list.slice(0, 15).map((f) => (
          <li key={f.id}>
            <button
              onClick={() => openChat(f.id)}
              className="flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left text-sm hover:bg-white"
            >
              <Avatar user={f} size={34} showOnline />
              <span className="truncate">{f.full_name}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function AppShell() {
  useRealtimeConnection();
  const user = useAuth((s) => s.user);
  const badges = useBadges();
  const items = navItems(user, badges);
  useEffect(() => {
    document.title = badges.notifications ? `(${badges.notifications}) MiniSocial` : 'MiniSocial';
  }, [badges.notifications]);

  return (
    <div className="min-h-screen pb-16 lg:pb-0">
      <TopBar />
      <div className="mx-auto flex max-w-7xl gap-6 px-3 py-5 sm:px-5">
        <nav className="sticky top-[76px] hidden h-fit w-56 shrink-0 lg:block" aria-label="Điều hướng chính">
          <ul className="space-y-0.5">
            {items.map((i) => (
              <li key={i.to}>
                <NavLink
                  to={i.to}
                  end={i.end}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-[15px] font-medium',
                      isActive ? 'bg-white text-ink shadow-card' : 'text-text hover:bg-white/70',
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <i.icon className={clsx('h-5 w-5', isActive ? 'text-amber-600' : 'text-muted')} />
                      {i.label}
                      <Badge n={i.badge} />
                    </>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
        <aside className="sticky top-[76px] hidden h-fit w-64 shrink-0 xl:block">
          <OnlineFriends />
        </aside>
      </div>
      <nav
        className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-white lg:hidden"
        aria-label="Điều hướng"
      >
        <ul className="flex">
          {items.slice(0, 5).map((i) => (
            <li key={i.to} className="flex-1">
              <NavLink
                to={i.to}
                end={i.end}
                className={({ isActive }) =>
                  clsx(
                    'relative flex flex-col items-center py-2 text-[11px]',
                    isActive ? 'text-ink' : 'text-muted',
                  )
                }
              >
                <i.icon className="h-5 w-5" />
                {i.label}
                {i.badge > 0 && <span className="absolute right-1/4 top-1 h-2 w-2 rounded-full bg-amber" />}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
