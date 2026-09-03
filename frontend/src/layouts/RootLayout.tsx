import { useEffect } from 'react'
import { Link, Outlet } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useUiStore } from '@/stores/ui-store'

export function RootLayout() {
  const theme = useUiStore((s) => s.theme)
  const toggleTheme = useUiStore((s) => s.toggleTheme)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-b">
        <nav className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <Link to="/" className="font-semibold">
            Classic Literature
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/books" className="text-muted-foreground text-sm">
              Books
            </Link>
            <Button variant="outline" size="sm" onClick={toggleTheme}>
              {theme === 'light' ? '🌙' : '☀️'}
            </Button>
          </div>
        </nav>
      </header>

      <main className="flex-1 px-4">
        <Outlet />
      </main>
    </div>
  )
}
