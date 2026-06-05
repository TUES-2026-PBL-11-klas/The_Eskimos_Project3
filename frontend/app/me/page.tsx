"use client";

import { useRouter } from "next/navigation";

import ReminderList from "@/components/ReminderList";
import { EmptyState } from "@/components/states";
import { useDemo } from "@/lib/demo/store";
import { formatDate } from "@/lib/format";

const LEAD_OPTIONS = [1, 2, 6, 12, 24, 48, 72];

export default function AccountPage() {
  const router = useRouter();
  const { hydrated, loggedIn, user, sessions, revokeSession, logout, updatePreferences } =
    useDemo();

  if (!hydrated) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <div className="skeleton mb-8 h-9 w-40 rounded" />
        <div className="skeleton h-64 w-full rounded-2xl" />
      </main>
    );
  }

  if (!loggedIn) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-20">
        <EmptyState
          icon="🔒"
          title="Log in to view your account"
          message="Manage your profile, devices and reminders once you're logged in."
          action={{ href: "/login", label: "Log in" }}
        />
      </main>
    );
  }

  const { preferences } = user;

  return (
    <main className="mx-auto max-w-3xl space-y-8 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-foreground">Account</h1>
        <button
          type="button"
          onClick={() => {
            logout();
            router.push("/");
          }}
          className="rounded-lg border border-border bg-surface px-4 py-2 text-sm font-semibold text-foreground transition hover:border-danger hover:text-danger"
        >
          Log out
        </button>
      </header>

      {/* Profile */}
      <section className="rounded-2xl border border-border bg-surface p-6">
        <h2 className="mb-4 text-lg font-semibold text-foreground">Profile</h2>
        <div className="flex items-center gap-4">
          <span className="grid h-14 w-14 place-items-center rounded-full bg-accent text-xl font-bold text-white">
            {user.display_name.charAt(0).toUpperCase()}
          </span>
          <div>
            <p className="font-semibold text-foreground">{user.display_name}</p>
            <p className="text-sm text-muted">{user.email}</p>
          </div>
        </div>
      </section>

      {/* Preferences */}
      <section className="rounded-2xl border border-border bg-surface p-6">
        <h2 className="mb-4 text-lg font-semibold text-foreground">Preferences</h2>
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs uppercase tracking-wide text-muted">Default reminder lead</dt>
            <dd className="mt-1.5">
              <select
                value={preferences.default_lead_hours}
                onChange={(e) => updatePreferences(Number(e.target.value))}
                className="rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm font-semibold text-foreground focus:border-accent focus:outline-none"
              >
                {LEAD_OPTIONS.map((h) => (
                  <option key={h} value={h}>
                    {h} hour{h === 1 ? "" : "s"} before
                  </option>
                ))}
              </select>
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-muted">Timezone</dt>
            <dd className="mt-1 font-semibold text-foreground">{preferences.timezone}</dd>
          </div>
        </dl>
      </section>

      {/* Active devices */}
      <section className="rounded-2xl border border-border bg-surface p-6">
        <h2 className="mb-4 text-lg font-semibold text-foreground">Active devices</h2>
        <ul className="space-y-3">
          {sessions.map((s) => (
            <li
              key={s.id}
              className="flex items-center justify-between gap-4 rounded-xl border border-border bg-surface-2 p-4"
            >
              <div>
                <p className="font-medium text-foreground">
                  {s.user_agent}
                  {s.current && (
                    <span className="ml-2 rounded-full bg-success/15 px-2 py-0.5 text-xs font-medium text-success">
                      This device
                    </span>
                  )}
                </p>
                <p className="mt-1 text-xs text-muted">
                  {s.ip ? `${s.ip} · ` : ""}since {formatDate(s.created_at)}
                </p>
              </div>
              {!s.current && (
                <button
                  type="button"
                  onClick={() => revokeSession(s.id)}
                  className="text-sm font-medium text-muted transition hover:text-danger"
                >
                  Revoke
                </button>
              )}
            </li>
          ))}
        </ul>
      </section>

      {/* Reminders */}
      <section className="rounded-2xl border border-border bg-surface p-6">
        <h2 className="mb-4 text-lg font-semibold text-foreground">Reminders</h2>
        <ReminderList />
      </section>
    </main>
  );
}
