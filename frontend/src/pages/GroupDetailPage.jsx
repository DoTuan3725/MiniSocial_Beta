import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Lock, Globe2, LogOut, Settings, UserPlus, Check, X } from 'lucide-react';
import { groupApi, postApi } from '../api/endpoints';
import PostCard from '../components/PostCard';
import PostComposer from '../components/PostComposer';
import { Avatar, EmptyState, LoadMore, Modal, PageLoader, Tabs, UserLink } from '../components/ui';
import { useCursorList } from '../hooks/useCursorList';
import { errorMessage } from '../lib/errors';
import { ROLE_LABEL, timeAgo } from '../lib/format';
import { useAuth } from '../store/auth';
import { toast } from '../store/toast';

const RANK = { MEMBER: 1, MOD: 2, ADMIN: 3 };

function Members({ group, myRole }) {
  const qc = useQueryClient();
  const me = useAuth((s) => s.user);
  const canModerate = RANK[myRole] >= 2;
  const members = useQuery({
    queryKey: ['group-members', group.id],
    queryFn: () => groupApi.members(group.id),
  });
  const pending = useQuery({
    queryKey: ['group-members', group.id, 'pending'],
    queryFn: () => groupApi.members(group.id, 'PENDING'),
    enabled: canModerate,
  });
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['group-members', group.id] });
    qc.invalidateQueries({ queryKey: ['group', group.id] });
  };
  const act = useMutation({
    mutationFn: ({ kind, m, role }) => {
      if (kind === 'approve') return groupApi.approve(group.id, m.id);
      if (kind === 'reject') return groupApi.reject(group.id, m.id);
      if (kind === 'kick') return groupApi.kick(group.id, m.id);
      return groupApi.setRole(group.id, m.id, role);
    },
    onSuccess: refresh,
    onError: (e) => toast.error(errorMessage(e)),
  });
  return (
    <div className="space-y-4">
      {canModerate && pending.data?.length > 0 && (
        <section className="card">
          <h2 className="border-b border-line px-4 py-3 font-semibold">
            Yêu cầu tham gia ({pending.data.length})
          </h2>
          <ul className="divide-y divide-line">
            {pending.data.map((m) => (
              <li key={m.id} className="flex items-center gap-3 px-4 py-3">
                <Avatar user={m.user} />
                <div className="flex-1">
                  <UserLink user={m.user} />
                  <p className="text-xs text-muted">Gửi {timeAgo(m.requested_at)}</p>
                </div>
                <button
                  className="btn-primary px-3"
                  onClick={() => act.mutate({ kind: 'approve', m })}
                  aria-label="Duyệt"
                >
                  <Check className="h-4 w-4" />
                </button>
                <button
                  className="btn-ghost px-3"
                  onClick={() => act.mutate({ kind: 'reject', m })}
                  aria-label="Từ chối"
                >
                  <X className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
      <section className="card">
        <h2 className="border-b border-line px-4 py-3 font-semibold">
          Thành viên ({members.data?.length || 0})
        </h2>
        {members.isError && <p className="p-4 text-sm text-muted">{errorMessage(members.error)}</p>}
        <ul className="divide-y divide-line">
          {(members.data || []).map((m) => (
            <li key={m.id} className="flex flex-wrap items-center gap-3 px-4 py-3">
              <Avatar user={m.user} showOnline />
              <div className="min-w-0 flex-1">
                <UserLink user={m.user} />
                <p className="text-xs text-muted">{ROLE_LABEL[m.role]}</p>
              </div>
              {myRole === 'ADMIN' && m.user.id !== me.id && (
                <select
                  className="rounded-lg border border-line px-2 py-1.5 text-sm"
                  value={m.role}
                  onChange={(e) => act.mutate({ kind: 'role', m, role: e.target.value })}
                  aria-label="Vai trò"
                >
                  {Object.entries(ROLE_LABEL).map(([v, l]) => (
                    <option key={v} value={v}>
                      {l}
                    </option>
                  ))}
                </select>
              )}
              {canModerate && m.user.id !== me.id && RANK[m.role] < RANK[myRole] && (
                <button
                  className="btn-danger px-3 py-1.5"
                  onClick={() =>
                    window.confirm(`Mời ${m.user.full_name} ra khỏi nhóm?`) && act.mutate({ kind: 'kick', m })
                  }
                >
                  Xóa
                </button>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function GroupSettings({ group, open, onClose }) {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: group.name,
    description: group.description,
    privacy: group.privacy,
  });
  const save = useMutation({
    mutationFn: () => groupApi.update(group.id, form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['group', group.id] });
      toast.success('Đã lưu thông tin nhóm');
      onClose();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  const remove = useMutation({
    mutationFn: () => groupApi.remove(group.id),
    onSuccess: () => {
      toast.success('Đã giải tán nhóm');
      qc.invalidateQueries({ queryKey: ['groups'] });
      navigate('/groups');
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  return (
    <Modal open={open} onClose={onClose} title="Cài đặt nhóm">
      <div className="space-y-4">
        <div>
          <label className="label">Tên nhóm</label>
          <input
            className="input"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>
        <div>
          <label className="label">Mô tả</label>
          <textarea
            className="input min-h-20"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>
        <div>
          <label className="label">Quyền riêng tư</label>
          <select
            className="input"
            value={form.privacy}
            onChange={(e) => setForm({ ...form, privacy: e.target.value })}
          >
            <option value="PUBLIC">Công khai</option>
            <option value="PRIVATE">Nhóm kín</option>
          </select>
        </div>
        <button className="btn-primary w-full" onClick={() => save.mutate()} disabled={save.isPending}>
          Lưu thay đổi
        </button>
        <button
          className="btn-danger w-full"
          onClick={() =>
            window.confirm('Giải tán nhóm? Toàn bộ bài viết trong nhóm sẽ bị xóa.') && remove.mutate()
          }
        >
          Giải tán nhóm
        </button>
      </div>
    </Modal>
  );
}

/** UC-18 -> UC-21: trang nhóm, tham gia/rời, duyệt, phân quyền, bài viết trong nhóm. */
export default function GroupDetailPage() {
  const { groupId } = useParams();
  const qc = useQueryClient();
  const [tab, setTab] = useState('posts');
  const [settings, setSettings] = useState(false);
  const group = useQuery({
    queryKey: ['group', groupId],
    queryFn: () => groupApi.detail(groupId),
    retry: false,
  });
  const membership = group.data?.my_membership;
  const isMember = membership?.status === 'ACCEPTED';
  const canView = group.data && (group.data.privacy === 'PUBLIC' || isMember);
  const posts = useCursorList(['group-posts', groupId], (c) => postApi.byGroup(groupId, c), {
    enabled: !!canView,
  });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['group', groupId] });
    qc.invalidateQueries({ queryKey: ['groups'] });
    qc.invalidateQueries({ queryKey: ['group-posts', groupId] });
  };
  const join = useMutation({
    mutationFn: () => groupApi.join(groupId),
    onSuccess: (d) => {
      toast.success(d.status === 'ACCEPTED' ? 'Đã tham gia nhóm' : 'Đã gửi yêu cầu, chờ quản trị viên duyệt');
      refresh();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  const leave = useMutation({
    mutationFn: () => groupApi.leave(groupId),
    onSuccess: () => {
      toast.success('Đã rời nhóm');
      refresh();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  if (group.isLoading) return <PageLoader />;
  if (group.isError) return <EmptyState title="Không tìm thấy nhóm" />;
  const g = group.data;

  return (
    <div className="mx-auto max-w-[760px] space-y-4">
      <section className="card overflow-hidden">
        <div className="h-32 bg-gradient-to-br from-ink to-ink-600 sm:h-44" />
        <div className="p-5">
          <h1 className="text-2xl font-bold">{g.name}</h1>
          <p className="mt-1 flex items-center gap-1.5 text-sm text-muted">
            {g.privacy === 'PRIVATE' ? <Lock className="h-4 w-4" /> : <Globe2 className="h-4 w-4" />}
            {g.privacy === 'PRIVATE' ? 'Nhóm kín' : 'Nhóm công khai'} · {g.members_count} thành viên
          </p>
          {g.description && <p className="mt-3 whitespace-pre-wrap text-sm">{g.description}</p>}
          <div className="mt-4 flex flex-wrap gap-2">
            {!membership || membership.status === 'REJECTED' ? (
              <button className="btn-primary" onClick={() => join.mutate()} disabled={join.isPending}>
                <UserPlus className="h-4 w-4" /> {g.privacy === 'PRIVATE' ? 'Xin tham gia' : 'Tham gia nhóm'}
              </button>
            ) : membership.status === 'PENDING' ? (
              <button className="btn-ghost" onClick={() => leave.mutate()}>
                Hủy yêu cầu tham gia
              </button>
            ) : (
              <button
                className="btn-ghost"
                onClick={() => window.confirm('Rời khỏi nhóm?') && leave.mutate()}
              >
                <LogOut className="h-4 w-4" /> Rời nhóm
              </button>
            )}
            {membership?.role === 'ADMIN' && isMember && (
              <button className="btn-ghost" onClick={() => setSettings(true)}>
                <Settings className="h-4 w-4" /> Cài đặt
              </button>
            )}
          </div>
        </div>
        <div className="px-3">
          <Tabs
            value={tab}
            onChange={setTab}
            tabs={[
              { value: 'posts', label: 'Thảo luận' },
              { value: 'members', label: 'Thành viên' },
            ]}
          />
        </div>
      </section>

      {!canView ? (
        <EmptyState icon={Lock} title="Đây là nhóm kín">
          Tham gia nhóm và chờ quản trị viên duyệt để xem bài viết.
        </EmptyState>
      ) : tab === 'posts' ? (
        <div className="space-y-4">
          {isMember && <PostComposer groupId={groupId} invalidateKeys={[['group-posts', groupId]]} />}
          {posts.items.map((p) => (
            <PostCard key={p.id} post={p} queryKeys={[['group-posts', groupId]]} />
          ))}
          {posts.isSuccess && posts.items.length === 0 && <EmptyState title="Nhóm chưa có bài viết nào" />}
          <LoadMore query={posts} />
        </div>
      ) : (
        <Members group={g} myRole={isMember ? membership.role : null} />
      )}
      {settings && <GroupSettings group={g} open={settings} onClose={() => setSettings(false)} />}
    </div>
  );
}
