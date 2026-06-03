import Navbar from "@/components/Navbar";

export default function EventPage() {
  // Example event data (later you can replace with API or database)
  const event = {
    name: "Tech Conference 2026",
    description:
      "Join industry leaders and developers for a full day of talks, workshops, and networking focused on modern web development, AI, and cloud technologies.",
    startTime: "2026-06-15 10:00 AM",
    endTime: "2026-06-15 06:00 PM",
    venue: "Sofia Tech Park, Bulgaria",
    price: "€49",
  };

  return (
    <main className="min-h-screen bg-gray-100 flex flex-col">
      <Navbar />

      <section className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-3xl bg-white rounded-2xl shadow-xl p-8">
          {/* Title */}
          <h1 className="text-4xl font-bold text-black">
            {event.name}
          </h1>

          {/* Description */}
          <p className="mt-4 text-gray-600 leading-relaxed">
            {event.description}
          </p>

          {/* Details Grid */}
          <div className="mt-8 grid md:grid-cols-2 gap-6">
            <div className="p-4 border rounded-xl">
              <p className="text-sm text-gray-500">Start Time</p>
              <p className="text-black font-semibold">
                {event.startTime}
              </p>
            </div>

            <div className="p-4 border rounded-xl">
              <p className="text-sm text-gray-500">End Time</p>
              <p className="text-black font-semibold">
                {event.endTime}
              </p>
            </div>

            <div className="p-4 border rounded-xl">
              <p className="text-sm text-gray-500">Venue</p>
              <p className="text-black font-semibold">
                {event.venue}
              </p>
            </div>

            <div className="p-4 border rounded-xl">
              <p className="text-sm text-gray-500">Price</p>
              <p className="text-black font-semibold">
                {event.price}
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-10 flex justify-between items-center">
           

            <button className="bg-black text-white px-6 py-3 rounded-xl font-semibold hover:bg-gray-800 transition">
              Mark in calendar
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}