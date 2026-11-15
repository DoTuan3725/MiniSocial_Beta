import { Logo } from '../../components/ui';

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_minmax(420px,520px)]">
      <section
        className="relative hidden overflow-hidden bg-ink p-12 text-white lg:flex lg:flex-col lg:justify-between"
        aria-hidden="true"
      >
        <svg className="absolute inset-0 h-full w-full opacity-[0.08]">
          <defs>
            <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
              <path d="M32 0H0V32" fill="none" stroke="white" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
        <div className="relative flex items-center gap-2 text-lg font-bold">
          <span className="h-3 w-3 rounded-sm bg-amber" /> MiniSocial
        </div>
        <div className="relative max-w-md">
          <p className="text-4xl font-bold leading-tight">
            Nơi sinh viên kết nối, chia sẻ và làm việc cùng nhau.
          </p>
          <p className="mt-4 text-white/70">
            Bảng tin bạn bè, nhóm học tập và nhắn tin tức thì trong một ứng dụng.
          </p>
        </div>
        <p className="relative text-sm text-white/50">Nhóm 1 · Đồ án HP 608819 · Đại học Xây dựng Hà Nội</p>
      </section>
      <section className="flex items-center justify-center bg-white px-6 py-10">
        <div className="w-full max-w-sm">
          <Logo className="mb-8 lg:hidden" />
          <h1 className="text-2xl font-bold">{title}</h1>
          {subtitle && <p className="mt-1.5 text-sm text-muted">{subtitle}</p>}
          <div className="mt-6">{children}</div>
          {footer && <div className="mt-6 text-center text-sm text-muted">{footer}</div>}
        </div>
      </section>
    </div>
  );
}

export function FormError({ message }) {
  if (!message) return null;
  return (
    <p role="alert" className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">
      {message}
    </p>
  );
}

export function OtpInput({ value, onChange }) {
  return (
    <input
      className="input text-center text-2xl font-semibold tracking-[0.5em]"
      inputMode="numeric"
      autoComplete="one-time-code"
      maxLength={6}
      value={value}
      onChange={(e) => onChange(e.target.value.replace(/\D/g, '').slice(0, 6))}
      placeholder="••••••"
      aria-label="Mã OTP 6 chữ số"
    />
  );
}
