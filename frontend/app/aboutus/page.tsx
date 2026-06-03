import Navbar from "@/components/Navbar";

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-gray-100 flex flex-col">
      <Navbar />

      {/* Hero Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-black">
            About EventHub
          </h1>

          <p className="mt-6 text-gray-600 text-lg leading-relaxed">
            EventHub is your all-in-one platform for discovering, creating,
            and managing events. From concerts and conferences to workshops
            and private gatherings, we make it easy to bring people together.
          </p>
        </div>
      </section>

      {/* Mission Section */}
      <section className="bg-white py-16 px-6">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-10 items-center">
          <div>
            <h2 className="text-3xl font-bold text-black mb-4">
              Our Mission
            </h2>

            <p className="text-gray-600 leading-relaxed">
              At EventHub, our mission is to simplify event discovery and
              creation. We believe that great experiences should be easy to
              access, whether you're attending a global conference or a local
              meetup.
            </p>

            <p className="text-gray-600 leading-relaxed mt-4">
              We empower organizers with powerful tools and give attendees a
              seamless way to explore events they love.
            </p>
          </div>

          <div className="rounded-2xl shadow p-8 border">
            <h3 className="text-xl font-semibold text-black mb-3">
              Why EventHub?
            </h3>

            <ul className="space-y-3 text-gray-600">
              <li>🎟 Discover events near you instantly</li>
              <li>📅 Easy event creation and management</li>
              <li>🔔 Real-time updates and reminders</li>
              <li>🌍 Built for global and local communities</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-6">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          <div>
            <h3 className="text-3xl font-bold text-black">10K+</h3>
            <p className="text-gray-600 mt-1">Events Hosted</p>
          </div>

          <div>
            <h3 className="text-3xl font-bold text-black">500K+</h3>
            <p className="text-gray-600 mt-1">Attendees</p>
          </div>

          <div>
            <h3 className="text-3xl font-bold text-black">120+</h3>
            <p className="text-gray-600 mt-1">Cities</p>
          </div>

          <div>
            <h3 className="text-3xl font-bold text-black">24/7</h3>
            <p className="text-gray-600 mt-1">Support</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-white py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-black">
            Ready to explore events?
          </h2>

          <p className="mt-4 text-gray-600">
            Join EventHub today and never miss an event again.
          </p>

          <div className="mt-8">
            <a
              href="/signup"
              className="bg-black text-white px-8 py-3 rounded-xl font-semibold hover:bg-gray-800 transition"
            >
              Get Started
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}