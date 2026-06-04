import { EmptyState } from "@/components/states";

export default function EventNotFound() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-20">
      <EmptyState
        icon="🔍"
        title="Event not found"
        message="This event doesn't exist or may have been removed."
        action={{ href: "/events", label: "Browse all events" }}
      />
    </main>
  );
}
