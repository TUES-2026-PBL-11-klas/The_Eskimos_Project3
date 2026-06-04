import Link from "next/link";

import type { Category } from "@/lib/api/types";
import { categoryStyle } from "@/lib/categories";

// Each tile links to the all-events list pre-filtered by that category.
export default function CategoryGrid({ categories }: { categories: Category[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {categories.map((c) => {
        const style = categoryStyle(c.name);
        return (
          <Link
            key={c.slug}
            href={`/events?category=${encodeURIComponent(c.name)}`}
            className="group flex flex-col gap-3 rounded-2xl border border-border bg-surface p-5 transition hover:-translate-y-0.5 hover:border-accent/60 hover:bg-surface-2"
          >
            <span
              className="grid h-11 w-11 place-items-center rounded-xl text-xl"
              style={{ background: style.tint }}
            >
              {style.icon}
            </span>
            <div>
              <p className="font-semibold text-foreground group-hover:text-accent-hover">
                {c.name}
              </p>
              <p className="text-sm text-muted">
                {c.count} {c.count === 1 ? "event" : "events"}
              </p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
