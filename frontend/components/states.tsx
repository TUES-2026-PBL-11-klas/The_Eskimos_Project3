// Shared empty / error / loading-skeleton building blocks.

import Link from "next/link";

export function EmptyState({
  icon = "🗓️",
  title,
  message,
  action,
}: {
  icon?: string;
  title: string;
  message?: string;
  action?: { href: string; label: string };
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-surface px-6 py-16 text-center">
      <div className="mb-3 text-4xl">{icon}</div>
      <h3 className="text-lg font-semibold text-foreground">{title}</h3>
      {message && <p className="mt-1 max-w-sm text-sm text-muted">{message}</p>}
      {action && (
        <Link
          href={action.href}
          className="mt-5 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-hover"
        >
          {action.label}
        </Link>
      )}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message = "We couldn't load this right now. Please try again.",
  retry,
}: {
  title?: string;
  message?: string;
  retry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-danger/40 bg-danger/5 px-6 py-16 text-center">
      <div className="mb-3 text-4xl">⚠️</div>
      <h3 className="text-lg font-semibold text-foreground">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-muted">{message}</p>
      {retry && (
        <button
          onClick={retry}
          className="mt-5 rounded-lg border border-border bg-surface px-4 py-2 text-sm font-semibold text-foreground transition hover:border-accent"
        >
          Try again
        </button>
      )}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="skeleton mb-4 h-5 w-20 rounded-full" />
      <div className="skeleton mb-2 h-5 w-3/4 rounded" />
      <div className="skeleton mb-4 h-5 w-1/2 rounded" />
      <div className="skeleton h-4 w-2/3 rounded" />
    </div>
  );
}

export function EventListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}
