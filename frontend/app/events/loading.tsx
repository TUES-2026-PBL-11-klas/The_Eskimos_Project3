import { EventListSkeleton } from "@/components/states";

export default function Loading() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="skeleton mb-2 h-9 w-48 rounded" />
      <div className="skeleton mb-8 h-4 w-28 rounded" />
      <EventListSkeleton count={9} />
    </main>
  );
}
