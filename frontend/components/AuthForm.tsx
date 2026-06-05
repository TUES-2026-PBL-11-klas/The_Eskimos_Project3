"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useDemo } from "@/lib/demo/store";

const MIN_PASSWORD = 8;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Mode = "login" | "register";
type FieldErrors = Partial<Record<"name" | "email" | "password" | "confirm", string>>;

const COPY = {
  login: {
    title: "Welcome back",
    subtitle: "Log in to save events and set reminders.",
    submit: "Log in",
    altText: "Don't have an account?",
    altHref: "/signup",
    altLabel: "Sign up",
  },
  register: {
    title: "Create your account",
    subtitle: "Save events, build a calendar and get reminders.",
    submit: "Sign up",
    altText: "Already have an account?",
    altHref: "/login",
    altLabel: "Log in",
  },
} as const;

export default function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const { login, register } = useDemo();
  const copy = COPY[mode];
  const isRegister = mode === "register";

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  function validate(): FieldErrors {
    const e: FieldErrors = {};
    if (isRegister && name.trim() === "") e.name = "Please enter your name.";
    if (email.trim() === "") e.email = "Please enter your email.";
    else if (!EMAIL_RE.test(email)) e.email = "Please enter a valid email.";
    if (password === "") e.password = "Please enter your password.";
    else if (isRegister && password.length < MIN_PASSWORD)
      e.password = `Password must be at least ${MIN_PASSWORD} characters.`;
    if (isRegister) {
      if (confirm === "") e.confirm = "Please confirm your password.";
      else if (confirm !== password) e.confirm = "Passwords do not match.";
    }
    return e;
  }

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    setFormError("");
    const fieldErrors = validate();
    setErrors(fieldErrors);
    if (Object.keys(fieldErrors).length > 0) return;

    setLoading(true);
    const result = isRegister
      ? await register(email, password, name.trim())
      : await login(email, password);

    if (result.ok) {
      setDone(true);
      // Authenticated session is set (httpOnly cookie); send the user home.
      router.push("/");
      return;
    }

    if (result.status === 409) setErrors({ email: result.error ?? "An account with this email already exists." });
    else if (result.status === 422) setFormError("Please check the highlighted fields.");
    else setFormError(result.error ?? "Something went wrong. Please try again.");
    setLoading(false);
  }

  const inputCls = (hasError?: string) =>
    `w-full rounded-xl border bg-surface-2 px-4 py-3 text-foreground placeholder:text-muted focus:outline-none focus:ring-2 ${
      hasError
        ? "border-danger focus:ring-danger/50"
        : "border-border focus:ring-accent/50 focus:border-accent"
    }`;

  return (
    <main className="mx-auto flex max-w-md flex-col justify-center px-6 py-16">
      <div className="rounded-2xl border border-border bg-surface p-8 shadow-xl">
        <h1 className="text-center text-2xl font-bold text-foreground">{copy.title}</h1>
        <p className="mt-2 text-center text-sm text-muted">{copy.subtitle}</p>

        <form className="mt-7 space-y-4" onSubmit={handleSubmit} noValidate>
          {isRegister && (
            <Field label="Name" error={errors.name}>
              <input
                type="text"
                placeholder="Jane Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={inputCls(errors.name)}
                autoComplete="name"
              />
            </Field>
          )}

          <Field label="Email" error={errors.email}>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputCls(errors.email)}
              autoComplete="email"
            />
          </Field>

          <Field label="Password" error={errors.password}>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputCls(errors.password)}
                autoComplete={isRegister ? "new-password" : "current-password"}
              />
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted hover:text-foreground"
                tabIndex={-1}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </Field>

          {isRegister && (
            <Field label="Confirm password" error={errors.confirm}>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className={inputCls(errors.confirm)}
                autoComplete="new-password"
              />
            </Field>
          )}

          {formError && (
            <div className="rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
              {formError}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || done}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent py-3 font-semibold text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-70"
          >
            {(loading || done) && (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            )}
            {done ? "Success" : loading ? "Please wait…" : copy.submit}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          {copy.altText}{" "}
          <Link href={copy.altHref} className="font-semibold text-accent hover:text-accent-hover">
            {copy.altLabel}
          </Link>
        </p>
      </div>
    </main>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-foreground">{label}</label>
      {children}
      {error && <p className="mt-1.5 text-sm text-danger">{error}</p>}
    </div>
  );
}
