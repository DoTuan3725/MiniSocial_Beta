import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../../api/endpoints';
import { errorMessage } from '../../lib/errors';
import { toast } from '../../store/toast';
import AuthLayout, { FormError, OtpInput } from './AuthLayout';
import { useCountdown } from './useCountdown';

/** UC-06: quên mật khẩu -> OTP qua email -> đặt mật khẩu mới (mọi phiên cũ bị đăng xuất). */
export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [cooldown, setCooldown] = useCountdown(0);

  const request = useMutation({
    mutationFn: () => authApi.forgot(email),
    onSuccess: () => {
      setStep(2);
      setCooldown(60);
      setError('');
    },
    onError: (e) => setError(errorMessage(e)),
  });
  const reset = useMutation({
    mutationFn: () => authApi.reset({ email, otp, new_password: password }),
    onSuccess: () => {
      toast.success('Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới.');
      navigate('/login');
    },
    onError: (e) => setError(errorMessage(e)),
  });

  return (
    <AuthLayout
      title="Quên mật khẩu"
      subtitle={
        step === 1 ? 'Nhập email đã đăng ký để nhận mã đặt lại mật khẩu.' : `Nhập mã đã gửi tới ${email}.`
      }
      footer={
        <Link to="/login" className="font-semibold text-ink hover:underline">
          Quay lại đăng nhập
        </Link>
      }
    >
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          setError('');
          if (step === 1) request.mutate();
          else reset.mutate();
        }}
      >
        {step === 1 ? (
          <div>
            <label className="label" htmlFor="f-email">
              Email
            </label>
            <input
              id="f-email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        ) : (
          <>
            <OtpInput value={otp} onChange={setOtp} />
            <div>
              <label className="label" htmlFor="new-password">
                Mật khẩu mới
              </label>
              <input
                id="new-password"
                type="password"
                className="input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
              <p className="mt-1 text-xs text-muted">
                Tối thiểu 8 ký tự, có chữ in hoa, chữ số và ký tự đặc biệt.
              </p>
            </div>
            <button
              type="button"
              className="text-sm text-ink hover:underline disabled:text-muted disabled:no-underline"
              disabled={cooldown > 0}
              onClick={() => request.mutate()}
            >
              {cooldown > 0 ? `Gửi lại mã sau ${cooldown}s` : 'Gửi lại mã'}
            </button>
          </>
        )}
        <FormError message={error} />
        <button className="btn-primary w-full py-2.5" disabled={request.isPending || reset.isPending}>
          {step === 1 ? 'Gửi mã' : 'Đặt lại mật khẩu'}
        </button>
      </form>
    </AuthLayout>
  );
}
