import { useEffect, useState } from 'react'
import Analytics from './pages/Analytics'
import Dashboard from './pages/Dashboard'
import Exam from './pages/Exam'
import Flashcards from './pages/Flashcards'
import Grammar from './pages/Grammar'
import Kanji from './pages/Kanji'
import Kaiwa from './pages/Kaiwa'
import Library from './pages/Library'
import Numbers from './pages/Numbers'
import Review from './pages/Review'
import Vocabulary from './pages/Vocabulary'

// Only implemented modules appear here (no placeholder screens).
const ROUTES = [
  { id: 'dashboard', label: 'Tổng quan', el: Dashboard },
  { id: 'vocabulary', label: 'Từ vựng', el: Vocabulary },
  { id: 'grammar', label: 'Ngữ pháp', el: Grammar },
  { id: 'kanji', label: 'Kanji', el: Kanji },
  { id: 'numbers', label: 'Số đếm', el: Numbers },
  { id: 'kaiwa', label: 'Hội thoại', el: Kaiwa },
  { id: 'flashcards', label: 'Ôn tập SRS', el: Flashcards },
  { id: 'exam', label: 'Thi thử', el: Exam },
  { id: 'analytics', label: 'Thống kê', el: Analytics },
  { id: 'review', label: 'Duyệt dữ liệu', el: Review },
  { id: 'library', label: 'Thư viện nguồn', el: Library },
] as const

function useHashRoute() {
  const read = () => location.hash.replace(/^#\/?/, '').split('?')[0] || 'dashboard'
  const [route, setRoute] = useState(read)
  useEffect(() => {
    const on = () => setRoute(read())
    addEventListener('hashchange', on)
    return () => removeEventListener('hashchange', on)
  }, [])
  return route
}

function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))
  return (
    <button type="button" aria-label="Đổi giao diện sáng/tối" title="Đổi giao diện sáng/tối"
      className="rounded-lg px-2 py-1 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
      onClick={() => {
        const next = !dark
        document.documentElement.classList.toggle('dark', next)
        try { localStorage.setItem('theme', next ? 'dark' : 'light') } catch { /* storage blocked */ }
        setDark(next)
      }}>
      {dark ? '☀︎ Sáng' : '☾ Tối'}
    </button>
  )
}

export default function App() {
  const route = useHashRoute()
  const current = ROUTES.find(r => r.id === route) ?? ROUTES[0]
  const Page = current.el
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-900/90">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-2">
          <a href="#/dashboard" className="flex shrink-0 items-center gap-2 font-semibold">
            <span className="jp rounded-md bg-indigo-600 px-1.5 text-white">日</span>
            <span className="hidden sm:inline">N5 Learning Hub</span>
          </a>
          <nav className="flex flex-1 gap-1 overflow-x-auto" aria-label="Điều hướng chính">
            {ROUTES.map(r => (
              <a key={r.id} href={`#/${r.id}`} aria-current={r.id === current.id ? 'page' : undefined}
                className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${r.id === current.id
                  ? 'bg-indigo-50 font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-200'
                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'}`}>
                {r.label}
              </a>
            ))}
          </nav>
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Page />
      </main>
    </div>
  )
}
