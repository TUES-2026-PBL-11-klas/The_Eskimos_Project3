import Link from "next/link";

export default function Navbar() {
  return (
    <header className="w-full bg-white shadow-sm">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-black">
          EventHub
        </h1>

        <nav className="flex gap-6 text-sm">
          <Link href="/" className="text-gray-700 hover:text-black">
            Home
          </Link>

          <Link href="/aboutus" className="text-gray-700 hover:text-black">
            About us
          </Link>

          <Link href="/login" className="text-gray-700 hover:text-black">
            Login
          </Link>
        </nav>
      </div>
    </header>
  );
}