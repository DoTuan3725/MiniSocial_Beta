import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Lock, Globe2, UsersRound, Search } from 'lucide-react';
import { groupApi } from '../api/endpoints';
import { EmptyState, Modal, PageLoader, Tabs } from '../components/ui';
import { useDebounced } from '../hooks/useDebounced';
import { errorMessage } from '../lib/errors';
import { toast } from '../store/toast';

function CreateGroup({ open, onClose }) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: '', description: '', privacy: 'PUBLIC' });
  const m = useMutation({
    mutationFn: () => groupApi.create(form),
    onSuccess: (g) => {
      qc.invalidateQueries({ queryKey: ['groups'] });
      toast.success('Đã tạo nhóm');
      navigate(`/groups/${g.id}`);
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  return (
    <Modal open={open} onClose={onClose} title="Tạo nhóm mới">
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          m.mutate();
        }}
      >
        <div>
          <label className="label">Tên nhóm</label>
          <input
            className="input"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
            maxLength={100}
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
        <fieldset className="grid grid-cols-2 gap-2">
          <legend className="label">Quyền riêng tư</legend>
          {[
            { v: 'PUBLIC', t: 'Công khai', d: 'Ai cũng xem và tham gia ngay', I: Globe2 },
            { v: 'PRIVATE', t: 'Nhóm kín', d: 'Phải được duyệt mới xem bài', I: Lock },
          ].map((o) => (
            <label
              key={o.v}
              className="cursor-pointer rounded-lg border border-line p-3 text-sm has-[:checked]:border-ink has-[:checked]:bg-ink-50"
            >
              <input
                type="radio"
                className="sr-only"
                checked={form.privacy === o.v}
                onChange={() => setForm({ ...form, privacy: o.v })}
              />
              <o.I className="mb-1 h-4 w-4 text-ink" />
              <span className="block font-semibold">{o.t}</span>
              <span className="text-xs text-muted">{o.d}</span>
            </label>
          ))}
        </fieldset>
        <button className="btn-primary w-full" disabled={m.isPending}>
          Tạo nhóm
        </button>
      </form>
    </Modal>
  );
}

/** UC-17: danh sách nhóm / nhóm của tôi / tạo nhóm. */
export default function GroupsPage() {
  const [tab, setTab] = useState('mine');
  const [creating, setCreating] = useState(false);
  const [q, setQ] = useState('');
  const term = useDebounced(q.trim());
  const groups = useQuery({
    queryKey: ['groups', tab, term],
    queryFn: () => groupApi.list({ ...(tab === 'mine' ? { mine: 1 } : {}), ...(term ? { q: term } : {}) }),
  });
  return (
    <div className="mx-auto max-w-[760px] space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Nhóm</h1>
        <button className="btn-primary" onClick={() => setCreating(true)}>
          <Plus className="h-4 w-4" /> Tạo nhóm
        </button>
      </div>
      <div className="card px-2">
        <Tabs
          value={tab}
          onChange={setTab}
          tabs={[
            { value: 'mine', label: 'Nhóm của tôi' },
            { value: 'all', label: 'Khám phá' },
          ]}
        />
        <div className="relative p-3">
          <Search className="absolute left-6 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            className="input pl-9"
            placeholder="Tìm nhóm"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Tìm nhóm"
          />
        </div>
      </div>
      {groups.isLoading && <PageLoader />}
      {groups.isSuccess && groups.data.length === 0 && (
        <EmptyState
          icon={UsersRound}
          title={tab === 'mine' ? 'Bạn chưa tham gia nhóm nào' : 'Không có nhóm phù hợp'}
        >
          Tham gia nhóm để trao đổi với những người cùng mối quan tâm.
        </EmptyState>
      )}
      <ul className="grid gap-3 sm:grid-cols-2">
        {(groups.data || []).map((g) => (
          <li key={g.id}>
            <Link
              to={`/groups/${g.id}`}
              className="card block overflow-hidden hover:ring-2 hover:ring-ink/10"
            >
              <div className="h-20 bg-gradient-to-br from-ink to-ink-600" />
              <div className="p-4">
                <p className="truncate font-semibold">{g.name}</p>
                <p className="mt-1 flex items-center gap-1.5 text-xs text-muted">
                  {g.privacy === 'PRIVATE' ? (
                    <Lock className="h-3.5 w-3.5" />
                  ) : (
                    <Globe2 className="h-3.5 w-3.5" />
                  )}
                  {g.privacy === 'PRIVATE' ? 'Nhóm kín' : 'Công khai'} · {g.members_count} thành viên
                </p>
                {g.my_membership?.status === 'PENDING' && (
                  <span className="mt-2 inline-block rounded bg-amber-50 px-2 py-0.5 text-xs text-ink-900">
                    Đang chờ duyệt
                  </span>
                )}
              </div>
            </Link>
          </li>
        ))}
      </ul>
      {creating && <CreateGroup open={creating} onClose={() => setCreating(false)} />}
    </div>
  );
}
