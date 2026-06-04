"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

// Debounced search input.
//  - autoNavigate=true (the /search page): live-filters by replacing the URL as
//    the user types (350ms debounce).
//  - autoNavigate=false (the header): only navigates to /search on submit/Enter.
export default function SearchBar({
  defaultValue = "",
  placeholder = "Search events…",
  autoNavigate = false,
  autoFocus = false,
  className = "",
}: {
  defaultValue?: string;
  placeholder?: string;
  autoNavigate?: boolean;
  autoFocus?: boolean;
  className?: string;
}) {
  const router = useRouter();
  const [value, setValue] = useState(defaultValue);
  const firstRun = useRef(true);

  useEffect(() => {
    if (!autoNavigate) return;
    if (firstRun.current) {
      firstRun.current = false;
      return;
    }
    const t = setTimeout(() => {
      const q = value.trim();
      router.replace(q ? `/search?q=${encodeURIComponent(q)}` : "/search");
    }, 350);
    return () => clearTimeout(t);
  }, [value, autoNavigate, router]);

  return (
    <form
      role="search"
      onSubmit={(e) => {
        e.preventDefault();
        const q = value.trim();
        router.push(q ? `/search?q=${encodeURIComponent(q)}` : "/search");
      }}
      className={`relative ${className}`}
    >
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted">
        🔍
      </span>
      <input
        type="search"
        autoFocus={autoFocus}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        aria-label="Search events"
        className="w-full rounded-xl border border-border bg-surface py-2.5 pl-9 pr-3 text-sm text-foreground placeholder:text-muted focus:border-accent focus:outline-none"
      />
    </form>
  );
}
