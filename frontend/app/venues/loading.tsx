export default function Loading() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="skeleton mb-2 h-9 w-32 rounded" />
      <div className="skeleton mb-8 h-4 w-64 rounded" />
      {Array.from({ length: 2 }).map((_, s) => (
        <div key={s} className="mb-10">
          <div className="skeleton mb-4 h-6 w-28 rounded" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="skeleton h-20 rounded-2xl" />
            ))}
          </div>
        </div>
      ))}
    </main>
  );
}
