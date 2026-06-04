"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useDemo } from "@/lib/demo/store";
import SearchBar from "./SearchBar";

const PUBLIC_NAV = [
  { href: "/events", label: "Events" },
  { href: "/venues", label: "Venues" },
  { href: "/about", label: "About" },
];

const AUTHED_NAV = [
  { href: "/me/saved", label: "Saved" },
  { href: "/me/calendar", label: "Calendar" },
  { href: "/me", label: "Account" },
];

export default function Header() {
  const pathname = usePathname();
  const { loggedIn, logout } = useDemo();

  // Exact match for index/account routes; prefix match for sections so that, e.g.,
  // "/events/123" highlights Events but "/me/saved" does not highlight Account.
  const isActive = (href: string) =>
    pathname === href || (href !== "/" && href !== "/me" && pathname.startsWith(href + "/"));

  const nav = loggedIn ? [...PUBLIC_NAV, ...AUTHED_NAV] : PUBLIC_NAV;

  const linkCls = (href: string, extra = "") =>
    `rounded-lg px-3 py-2 text-sm transition ${
      isActive(href)
        ? "bg-surface-2 text-foreground"
        : "text-muted hover:bg-surface hover:text-foreground"
    } ${extra}`;

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3.5">
        <Link href="/" className="flex items-center gap-2 font-bold text-foreground">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-sm text-white">
            EH
          </span>
          <span className="text-lg tracking-tight">EventHub</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {nav.map((item) => (
            <Link key={item.href} href={item.href} className={linkCls(item.href)}>
              {item.label}
            </Link>
          ))}
        </nav>

        <SearchBar className="hidden w-56 lg:block" placeholder="Search events…" />

        <div className="flex items-center gap-2">
          {loggedIn ? (
            <button
              type="button"
              onClick={logout}
              className="rounded-lg border border-border bg-surface px-3.5 py-2 text-sm font-semibold text-foreground transition hover:border-accent"
            >
              Log out
            </button>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-lg px-3 py-2 text-sm text-muted transition hover:text-foreground"
              >
                Login
              </Link>
              <Link
                href="/signup"
                className="rounded-lg bg-accent px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-accent-hover"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Mobile nav row */}
      <nav className="flex items-center gap-1 overflow-x-auto border-t border-border px-4 py-2 md:hidden">
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm transition ${
              isActive(item.href)
                ? "bg-surface-2 text-foreground"
                : "text-muted hover:text-foreground"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
