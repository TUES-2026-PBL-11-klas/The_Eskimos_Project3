"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

// URL-driven pagination. Preserves every other query param (filters, search)
// and only changes `page`, so it composes with the FilterBar filters.
export default function Pagination({ page, pages }: { page: number; pages: number }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  if (pages <= 1) return null;

  const href = (p: number) => {
    const params = new URLSearchParams(searchParams.toString());
    if (p <= 1) params.delete("page");
    else params.set("page", String(p));
    const qs = params.toString();
    return qs ? `${pathname}?${qs}` : pathname;
  };

  // Compact window of page numbers around the current page.
  const windowSize = 5;
  let start = Math.max(1, page - Math.floor(windowSize / 2));
  const end = Math.min(pages, start + windowSize - 1);
  start = Math.max(1, end - windowSize + 1);
  const numbers = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  const base =
    "inline-flex h-9 min-w-9 items-center justify-center rounded-lg border px-3 text-sm transition";

  return (
    <nav className="mt-8 flex items-center justify-center gap-1.5" aria-label="Pagination">
      <Link
        href={href(page - 1)}
        aria-disabled={page <= 1}
        tabIndex={page <= 1 ? -1 : undefined}
        className={`${base} border-border bg-surface text-muted hover:border-accent hover:text-foreground ${
          page <= 1 ? "pointer-events-none opacity-40" : ""
        }`}
      >
        ← Prev
      </Link>

      {numbers.map((n) => (
        <Link
          key={n}
          href={href(n)}
          aria-current={n === page ? "page" : undefined}
          className={`${base} ${
            n === page
              ? "border-accent bg-accent font-semibold text-white"
              : "border-border bg-surface text-muted hover:border-accent hover:text-foreground"
          }`}
        >
          {n}
        </Link>
      ))}

      <Link
        href={href(page + 1)}
        aria-disabled={page >= pages}
        tabIndex={page >= pages ? -1 : undefined}
        className={`${base} border-border bg-surface text-muted hover:border-accent hover:text-foreground ${
          page >= pages ? "pointer-events-none opacity-40" : ""
        }`}
      >
        Next →
      </Link>
    </nav>
  );
}
