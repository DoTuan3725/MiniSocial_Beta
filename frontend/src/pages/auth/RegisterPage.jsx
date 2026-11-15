import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../../api/endpoints';
import { errorMessage } from '../../lib/errors';
import AuthLayout, { FormError } from './AuthLayout';

const RULES = [
  { test: (p) => p.length >= 8, label: 'Ít nhất 8 ký tự' },
  { test: (p) => /[A-Z]/.test(p), label: 'Có chữ in hoa' },
  { test: (p) => /\d/.test(p), label: 'Có chữ số' },
  { test: (p) => /[^A-Za-z0-9]/.test(p), label: 'Có ký tự đặc biệt' },
];

/** UC-01: đăng ký -> nhận OTP qua email -> kích hoạt. */
export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: '', email: '', birth_date: '', password: '' });
  const [error, setError] = useState('');
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const strong = RULES.every((r) => r.test(form.password));
  const m = useMutation({
    mutationFn: () => authApi.register({ ...form, birth_date: form.birth_date || null }),
    onSuccess: () => navigate(`/verify-email?email=${encodeURIComponent(form.email)}&sent=1`),
    onError: (e) => setError(errorMessage(e)),
  });
  return (
    <AuthLayout
      title="Tạo tài khoản"
      subtitle="Chúng tôi sẽ gửi mã kích hoạt tới email của bạn."
      footer={
        <>
          Đã có tài khoản?{' '}
          <Link to="/login" className="font-semibold text-ink hover:underline">
            Đăng nhập
          </Link>
        </>
      }
    >
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          setError('');
          m.mutate();
        }}
      >
        <div>
          <label className="label" htmlFor="full_name">
            Họ và tên
          </label>
          <input
            id="full_name"
            className="input"
            value={form.full_name}
            onChange={set('full_name')}
            required
            maxLength={100}
            autoComplete="name"
          />
        </div>
        <div>
          <label className="label" htmlFor="reg-email">
            Email
          </label>
          <input
            id="reg-email"
            type="email"
            className="input"
            value={form.email}
            onChange={set('email')}
            required
            autoComplete="email"
          />
        </div>
        <div>
          <label className="label" htmlFor="birth_date">
            Ngày sinh
          </label>
          <input
            id="birth_date"
            type="date"
            className="input"
            value={form.birth_date}
            onChange={set('birth_date')}
          />
        </div>
        <div>
          <label className="label" htmlFor="reg-password">
            Mật khẩu
          </label>
          <input
            id="reg-password"
            type="password"
            className="input"
            value={form.password}
            onChange={set('password')}
            required
            autoComplete="new-password"
          />
          <ul className="mt-2 grid grid-cols-2 gap-1 text-xs">
            {RULES.map((r) => (
              <li key={r.label} className={r.test(form.password) ? 'text-success' : 'text-muted'}>
                {r.test(form.password) ? '✓' : '○'} {r.label}
              </li>
            ))}
          </ul>
        </div>
        <FormError message={error} />
        <button className="btn-primary w-full py-2.5" disabled={m.isPending || !strong}>
          Đăng ký
        </button>
      </form>
    </AuthLayout>
  );
}
