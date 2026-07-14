import { NavLink } from 'react-router-dom'

function Header() {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
        <a href="#" className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-brand-600 flex items-center justify-center">
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
          <span className="font-semibold text-base sm:text-lg tracking-tight">
            AI Educational Video Generator
          </span>
        </a>
        <nav className="flex items-center gap-6 text-sm">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? 'text-white transition-colors' : 'text-slate-400 hover:text-white transition-colors'
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/create"
            className={({ isActive }) =>
              isActive ? 'text-white transition-colors' : 'text-slate-400 hover:text-white transition-colors'
            }
          >
            Create Video
          </NavLink>
          <NavLink
            to="/library"
            className={({ isActive }) =>
              isActive ? 'text-white transition-colors' : 'text-slate-400 hover:text-white transition-colors'
            }
          >
            My Videos
          </NavLink>
        </nav>
      </div>
    </header>
  )
}

export default Header
