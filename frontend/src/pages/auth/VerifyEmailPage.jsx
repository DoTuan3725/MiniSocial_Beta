import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../../api/endpoints';
import { errorMessage } from '../../lib/errors';
import { useAuth } from '../../store/auth';
import { toast } from '../../store/toast';
import AuthLayout, { FormError, OtpInput } from './AuthLayout';
import { useCountdown } from './useCountdown';

/** UC-01: nhập mã OTP để kích hoạt tài khoản (mã sống 5 phút, gửi lại sau 60 giây). */
export default function VerifyEmailPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState(params.get('email') || '');
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [cooldown, setCooldown] = useCountdown(params.get('sent') ? 60 : 0);

  const verify = useMutation({
    mutationFn: () => authApi.verifyEmail({ email, otp }),
    onSuccess: (d) => {
      useAuth.getState().setSession(d.access_token, d.user);
      toast.success('Kích hoạt tài khoản thành công!');
      navigate('/', { replace: true });
    },
    onError: (e) => setError(errorMessage(e)),
  });
  const resend = useMutation({
    mutationFn: () => authApi.requestOtp(email, 'register'),
    onSuccess: (d) => {
      setCooldown(d.cooldown || 60);
      toast.success('Đã gửi lại mã kích hoạt');
    },
    onError: (e) => setError(errorMessage(e)),
  });

  return (
    <AuthLayout
      title="Kích hoạt tài khoản"
      subtitle="Nhập mã 6 chữ số chúng tôi vừa gửi tới email. Mã có hiệu lực trong 5 phút."
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
          verify.mutate();
        }}
      >
        <div>
          <label className="label" htmlFor="v-email">
            Email
          </label>
          <input
            id="v-email"
            type="email"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <OtpInput value={otp} onChange={setOtp} />
        <FormError message={error} />
        <button className="btn-primary w-full py-2.5" disabled={otp.length !== 6 || verify.isPending}>
          Kích hoạt
        </button>
        <button
          type="button"
          className="w-full text-sm text-ink hover:underline disabled:text-muted disabled:no-underline"
          disabled={!email || cooldown > 0 || resend.isPending}
          onClick={() => resend.mutate()}
        >
          {cooldown > 0 ? `Gửi lại mã sau ${cooldown}s` : 'Chưa nhận được mã? Gửi lại'}
        </button>
      </form>
    </AuthLayout>
  );
}
