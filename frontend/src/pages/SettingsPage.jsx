import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../api/endpoints';
import { errorMessage } from '../lib/errors';
import { useAuth } from '../store/auth';
import { toast } from '../store/toast';

/** UC-06: đổi mật khẩu khi đang đăng nhập (các thiết bị khác bị đăng xuất). */
export default function SettingsPage() {
  const user = useAuth((s) => s.user);
  const [form, setForm] = useState({ old_password: '', new_password: '', confirm: '' });
  const m = useMutation({
    mutationFn: () =>
      authApi.changePassword({ old_password: form.old_password, new_password: form.new_password }),
    onSuccess: (d) => {
      useAuth.getState().setSession(d.access_token, d.user);
      setForm({ old_password: '', new_password: '', confirm: '' });
      toast.success('Đã đổi mật khẩu. Các thiết bị khác đã bị đăng xuất.');
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const mismatch = form.confirm && form.confirm !== form.new_password;
  return (
    <div className="mx-auto max-w-[520px] space-y-4">
      <h1 className="text-xl font-bold">Cài đặt tài khoản</h1>
      <section className="card p-5">
        <h2 className="font-semibold">Thông tin đăng nhập</h2>
        <p className="mt-1 text-sm text-muted">Email: {user?.email}</p>
      </section>
      <section className="card p-5">
        <h2 className="mb-4 font-semibold">Đổi mật khẩu</h2>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            m.mutate();
          }}
        >
          <div>
            <label className="label">Mật khẩu hiện tại</label>
            <input
              type="password"
              className="input"
              value={form.old_password}
              onChange={set('old_password')}
              required
              autoComplete="current-password"
            />
          </div>
          <div>
            <label className="label">Mật khẩu mới</label>
            <input
              type="password"
              className="input"
              value={form.new_password}
              onChange={set('new_password')}
              required
              autoComplete="new-password"
            />
          </div>
          <div>
            <label className="label">Nhập lại mật khẩu mới</label>
            <input
              type="password"
              className="input"
              value={form.confirm}
              onChange={set('confirm')}
              required
              autoComplete="new-password"
            />
            {mismatch && <p className="mt-1 text-xs text-danger">Mật khẩu nhập lại không khớp</p>}
          </div>
          <button className="btn-primary" disabled={m.isPending || mismatch}>
            Đổi mật khẩu
          </button>
        </form>
      </section>
    </div>
  );
}
