import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../../api/endpoints';
import { Tabs } from '../../components/ui';
import { errorCode, errorMessage } from '../../lib/errors';
import { useAuth } from '../../store/auth';
import AuthLayout, { FormError, OtpInput } from './AuthLayout';
import { useCountdown } from './useCountdown';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [mode, setMode] = useState('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [cooldown, setCooldown] = useCountdown(0);
  const [error, setError] = useState('');

  const onLoggedIn = (data) => {
    useAuth.getState().setSession(data.access_token, data.user);
    navigate(location.state?.from || '/', { replace: true });
  };
  const onFail = (e) => {
    if (errorCode(e) === 'EMAIL_NOT_VERIFIED') {
      navigate(`/verify-email?email=${encodeURIComponent(email)}`);
      return;
    }
    setError(errorMessage(e));
  };

  const login = useMutation({
    mutationFn: () => authApi.login({ email, password }),
    onSuccess: onLoggedIn,
    onError: onFail,
  });
  const sendOtp = useMutation({
    mutationFn: () => authApi.requestOtp(email, 'login'),
    onSuccess: (d) => {
      setOtpSent(true);
      setCooldown(d.cooldown || 60);
      setError('');
    },
    onError: onFail,
  });
  const loginOtp = useMutation({
    mutationFn: () => authApi.loginOtp({ email, otp }),
    onSuccess: onLoggedIn,
    onError: onFail,
  });

  return (
    <AuthLayout
      title="Đăng nhập"
      subtitle="Chào mừng bạn quay lại."
      footer={
        <>
          Chưa có tài khoản?{' '}
          <Link to="/register" className="font-semibold text-ink hover:underline">
            Đăng ký
          </Link>
        </>
      }
    >
      <Tabs
        tabs={[
          { value: 'password', label: 'Mật khẩu' },
          { value: 'otp', label: 'Mã qua email' },
        ]}
        value={mode}
        onChange={(m) => {
          setMode(m);
          setError('');
        }}
      />
      <form
        className="mt-5 space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          setError('');
          if (mode === 'password') login.mutate();
          else if (!otpSent) sendOtp.mutate();
          else loginOtp.mutate();
        }}
      >
        <div>
          <label className="label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </div>
        {mode === 'password' ? (
          <div>
            <div className="flex items-center justify-between">
              <label className="label" htmlFor="password">
                Mật khẩu
              </label>
              <Link to="/forgot-password" className="mb-1.5 text-sm text-ink hover:underline">
                Quên mật khẩu?
              </Link>
            </div>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
        ) : (
          otpSent && (
            <div>
              <label className="label">Mã 6 chữ số đã gửi tới email</label>
              <OtpInput value={otp} onChange={setOtp} />
              <button
                type="button"
                className="mt-2 text-sm text-ink hover:underline disabled:text-muted disabled:no-underline"
                disabled={cooldown > 0 || sendOtp.isPending}
                onClick={() => sendOtp.mutate()}
              >
                {cooldown > 0 ? `Gửi lại mã sau ${cooldown}s` : 'Gửi lại mã'}
              </button>
            </div>
          )
        )}
        <FormError message={error} />
        <button
          className="btn-primary w-full py-2.5"
          disabled={
            login.isPending ||
            sendOtp.isPending ||
            loginOtp.isPending ||
            (mode === 'otp' && otpSent && otp.length !== 6)
          }
        >
          {mode === 'password' ? 'Đăng nhập' : otpSent ? 'Xác nhận mã' : 'Gửi mã đăng nhập'}
        </button>
      </form>
    </AuthLayout>
  );
}
