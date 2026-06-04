import Link from "next/link";

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-8 text-sm text-muted sm:flex-row">
        <p>© {new Date().getFullYear()} EventHub — events aggregated from across Bulgaria.</p>
        <nav className="flex gap-4">
          <Link href="/events" className="hover:text-foreground">
            Events
          </Link>
          <Link href="/venues" className="hover:text-foreground">
            Venues
          </Link>
          <Link href="/about" className="hover:text-foreground">
            About
          </Link>
        </nav>
      </div>
    </footer>
  );
}
