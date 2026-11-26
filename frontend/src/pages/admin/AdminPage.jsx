import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { ShieldCheck, Bot } from 'lucide-react';
import clsx from 'clsx';
import { adminApi } from '../../api/endpoints';
import { Avatar, EmptyState, LoadMore, Modal, PageLoader, Tabs, UserLink } from '../../components/ui';
import { useCursorList } from '../../hooks/useCursorList';
import { useDebounced } from '../../hooks/useDebounced';
import { errorMessage } from '../../lib/errors';
import { timeAgo } from '../../lib/format';
import { toast } from '../../store/toast';

function Stat({ label, value, tone }) {
  return (
    <div className="card p-4">
      <p className="text-sm text-muted">{label}</p>
      <p className={clsx('mt-1 text-2xl font-bold', tone === 'warn' ? 'text-amber-600' : 'text-ink')}>
        {value ?? '-'}
      </p>
    </div>
  );
}

function Dashboard() {
  const q = useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: adminApi.dashboard,
    refetchInterval: 60000,
  });
  if (q.isLoading) return <PageLoader />;
  const d = q.data;
  const days = Object.keys(d.new_users_per_day);
  const chart = days.map((day) => ({
    day: day.slice(5).split('-').reverse().join('/'),
    'Người dùng mới': d.new_users_per_day[day],
    'Bài viết mới': d.posts_per_day[day] || 0,
  }));
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Tổng người dùng" value={d.total_users} />
        <Stat label="Hoạt động hôm nay (DAU)" value={d.dau} />
        <Stat label="Hoạt động 30 ngày (MAU)" value={d.mau} />
        <Stat label="Tài khoản bị khóa" value={d.banned_users} />
        <Stat label="Bài viết" value={d.total_posts} />
        <Stat label="Bình luận" value={d.total_comments} />
        <Stat label="Nhóm" value={d.total_groups} />
        <Stat
          label="Báo cáo chờ xử lý"
          value={d.pending_reports}
          tone={d.pending_reports ? 'warn' : undefined}
        />
      </div>
      <section className="card p-4">
        <h2 className="mb-3 font-semibold">Tăng trưởng 14 ngày gần nhất</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#DDE3EA" />
              <XAxis dataKey="day" fontSize={12} />
              <YAxis allowDecimals={false} fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Người dùng mới" fill="#1F3A5F" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Bài viết mới" fill="#E8A33D" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

const ACTIONS = [
  { value: 'NONE', label: 'Ghi nhận, không xử phạt' },
  { value: 'DELETE_CONTENT', label: 'Gỡ nội dung' },
  { value: 'WARN_USER', label: 'Cảnh cáo người đăng' },
  { value: 'BAN_USER', label: 'Khóa tài khoản người đăng' },
];

function ResolveDialog({ report, onClose }) {
  const qc = useQueryClient();
  const [action, setAction] = useState(report.target_type === 'USER' ? 'BAN_USER' : 'DELETE_CONTENT');
  const [notes, setNotes] = useState('');
  const m = useMutation({
    mutationFn: (decision) => adminApi.resolve(report.id, { decision, action, notes }),
    onSuccess: () => {
      toast.success('Đã xử lý báo cáo');
      qc.invalidateQueries({ queryKey: ['admin'] });
      onClose();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  return (
    <Modal open onClose={onClose} title="Thẩm định báo cáo">
      <div className="space-y-4">
        <div className="rounded-lg bg-paper p-3 text-sm">
          <p className="font-semibold">{report.reason_label}</p>
          {report.details && <p className="mt-1 text-muted">{report.details}</p>}
          {report.target?.content && (
            <p className="mt-2 border-l-2 border-amber pl-2">{report.target.content}</p>
          )}
        </div>
        <fieldset className="space-y-2">
          <legend className="label">Biện pháp</legend>
          {ACTIONS.filter((a) => !(report.target_type === 'USER' && a.value === 'DELETE_CONTENT')).map(
            (a) => (
              <label key={a.value} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  className="accent-ink"
                  checked={action === a.value}
                  onChange={() => setAction(a.value)}
                />
                {a.label}
              </label>
            ),
          )}
        </fieldset>
        <div>
          <label className="label">Ghi chú (gửi kèm cảnh cáo)</label>
          <textarea className="input min-h-16" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <button className="btn-ghost" onClick={() => m.mutate('REJECTED')} disabled={m.isPending}>
            Bác bỏ báo cáo
          </button>
          <button className="btn-primary" onClick={() => m.mutate('RESOLVED')} disabled={m.isPending}>
            Xác nhận vi phạm
          </button>
        </div>
      </div>
    </Modal>
  );
}

function Reports() {
  const [status, setStatus] = useState('PENDING');
  const [active, setActive] = useState(null);
  const list = useCursorList(['admin', 'reports', status], (c) => adminApi.reports(status, c));
  const targetLink = (r) =>
    r.target_type === 'POST'
      ? `/posts/${r.target_id}`
      : r.target_type === 'USER'
        ? `/u/${r.target_id}`
        : r.target?.post_id && `/posts/${r.target.post_id}`;
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        {[
          ['PENDING', 'Chờ xử lý'],
          ['RESOLVED', 'Đã xử lý'],
          ['REJECTED', 'Đã bác bỏ'],
        ].map(([v, l]) => (
          <button key={v} className={status === v ? 'btn-primary' : 'btn-ghost'} onClick={() => setStatus(v)}>
            {l}
          </button>
        ))}
      </div>
      {list.isLoading && <PageLoader />}
      {list.isSuccess && list.items.length === 0 && (
        <EmptyState icon={ShieldCheck} title="Không có báo cáo nào" />
      )}
      <ul className="space-y-3">
        {list.items.map((r) => (
          <li key={r.id} className="card p-4">
            <div className="flex flex-wrap items-start gap-3">
              <span className="rounded bg-ink-50 px-2 py-0.5 text-xs font-semibold text-ink">
                {r.target_type}
              </span>
              <div className="min-w-0 flex-1 text-sm">
                <p className="font-semibold">{r.reason_label}</p>
                <p className="text-muted">
                  {r.is_auto ? (
                    <span className="inline-flex items-center gap-1">
                      <Bot className="h-3.5 w-3.5" /> Bộ lọc tự động
                    </span>
                  ) : (
                    <>
                      Báo cáo bởi <UserLink user={r.reporter} className="text-text" />
                    </>
                  )}{' '}
                  · {timeAgo(r.created_at)}
                </p>
                {r.reported_user && (
                  <p className="mt-1 flex items-center gap-2">
                    Người bị báo cáo: <Avatar user={r.reported_user} size={20} />{' '}
                    <UserLink user={r.reported_user} />
                  </p>
                )}
                {r.details && <p className="mt-1 text-muted">{r.details}</p>}
                {r.target?.content && <p className="mt-2 border-l-2 border-amber pl-2">{r.target.content}</p>}
                {r.status !== 'PENDING' && (
                  <p className="mt-2 text-xs text-muted">
                    {r.status === 'RESOLVED' ? `Đã xử lý: ${r.action_taken}` : 'Đã bác bỏ'} bởi{' '}
                    {r.resolved_by?.full_name}
                    {r.resolution_notes && ` · ${r.resolution_notes}`}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                {targetLink(r) && (
                  <Link className="btn-ghost" to={targetLink(r)}>
                    Xem
                  </Link>
                )}
                {r.status === 'PENDING' && (
                  <button className="btn-primary" onClick={() => setActive(r)}>
                    Xử lý
                  </button>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
      <LoadMore query={list} />
      {active && <ResolveDialog report={active} onClose={() => setActive(null)} />}
    </div>
  );
}

function UsersAdmin() {
  const qc = useQueryClient();
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const term = useDebounced(q.trim());
  const list = useCursorList(['admin', 'users', term, status], (c) =>
    adminApi.users({
      ...(term ? { q: term } : {}),
      ...(status ? { status } : {}),
      ...(c ? { cursor: c } : {}),
    }),
  );
  const m = useMutation({
    mutationFn: ({ u, ban }) => (ban ? adminApi.ban(u.id, '') : adminApi.unban(u.id)),
    onSuccess: () => {
      toast.success('Đã cập nhật trạng thái tài khoản');
      qc.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <input
          className="input max-w-xs"
          placeholder="Tìm theo tên hoặc email"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="rounded-lg border border-line px-3 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">Tất cả</option>
          <option value="active">Đang hoạt động</option>
          <option value="banned">Bị khóa</option>
          <option value="unverified">Chưa kích hoạt</option>
        </select>
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-line text-left text-muted">
            <tr>
              <th className="px-4 py-2.5 font-medium">Người dùng</th>
              <th className="px-4 py-2.5 font-medium">Trạng thái</th>
              <th className="px-4 py-2.5 font-medium">Bị báo cáo</th>
              <th className="px-4 py-2.5 font-medium">Đăng nhập gần nhất</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {list.items.map((u) => (
              <tr key={u.id}>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <Avatar user={u} size={32} />
                    <div>
                      <UserLink user={u} />
                      <p className="text-xs text-muted">{u.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-2.5">
                  {!u.is_active ? (
                    <span className="text-danger">Bị khóa</span>
                  ) : !u.email_verified ? (
                    <span className="text-muted">Chưa kích hoạt</span>
                  ) : (
                    <span className="text-success">Hoạt động</span>
                  )}
                  {u.role === 'ADMIN' && (
                    <span className="ml-2 rounded bg-amber-50 px-1.5 text-xs">ADMIN</span>
                  )}
                </td>
                <td className="px-4 py-2.5">{u.reports_received}</td>
                <td className="px-4 py-2.5 text-muted">{u.last_login ? timeAgo(u.last_login) : 'Chưa'}</td>
                <td className="px-4 py-2.5 text-right">
                  {u.role !== 'ADMIN' &&
                    (u.is_active ? (
                      <button
                        className="btn-danger px-3 py-1.5"
                        onClick={() =>
                          window.confirm(`Khóa tài khoản ${u.full_name}?`) && m.mutate({ u, ban: true })
                        }
                      >
                        Khóa
                      </button>
                    ) : (
                      <button className="btn-ghost px-3 py-1.5" onClick={() => m.mutate({ u, ban: false })}>
                        Mở khóa
                      </button>
                    ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <LoadMore query={list} />
    </div>
  );
}

/** UC-28: trang quản trị (thống kê, kiểm duyệt báo cáo, quản lý tài khoản). */
export default function AdminPage() {
  const [tab, setTab] = useState('dashboard');
  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <h1 className="text-xl font-bold">Quản trị hệ thống</h1>
      <div className="card px-2">
        <Tabs
          value={tab}
          onChange={setTab}
          tabs={[
            { value: 'dashboard', label: 'Thống kê' },
            { value: 'reports', label: 'Báo cáo vi phạm' },
            { value: 'users', label: 'Người dùng' },
          ]}
        />
      </div>
      {tab === 'dashboard' && <Dashboard />}
      {tab === 'reports' && <Reports />}
      {tab === 'users' && <UsersAdmin />}
    </div>
  );
}
