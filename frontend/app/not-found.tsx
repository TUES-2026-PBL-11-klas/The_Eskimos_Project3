import { EmptyState } from "@/components/states";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <EmptyState
        icon="🧭"
        title="Page not found"
        message="The page you're looking for doesn't exist."
        action={{ href: "/", label: "Go home" }}
      />
    </main>
  );
}
