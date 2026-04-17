"use client";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        {/* Logo + wordmark */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white font-bold text-sm">
            MR
          </div>
          <div>
            <h1 className="text-base font-bold text-gray-900 leading-tight">Munich Rental</h1>
            <p className="text-xs text-gray-400 leading-tight">Assistant</p>
          </div>
        </div>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-6">
          <a href="/" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors">
            🏠 Listings
          </a>
          <a href="/profile" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors">
            👤 Profile
          </a>
          <a href="/docs" className="text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors">
            📋 Docs
          </a>
        </nav>

        {/* Status badge */}
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
          </span>
          <span className="text-xs text-gray-500">Live</span>
        </div>
      </div>
    </header>
  );
}
