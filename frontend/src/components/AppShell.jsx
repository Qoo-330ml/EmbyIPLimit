import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'

import { Button } from '@/components/ui/button'

const navItems = [
  { to: '/', label: '首页' },
  { to: '/admin/users', label: '管理后台' },
]

const adminSubNav = [
  { to: '/admin/users', label: '用户' },
  { to: '/admin/config', label: '配置' },
  { to: '/admin/groups', label: '用户组' },
]

export default function AppShell() {
  const location = useLocation()
  const [theme, setTheme] = useState('light')

  useEffect(() => {
    const saved = localStorage.getItem('emby-ui-theme')
    const initial = saved || 'light'
    setTheme(initial)
    document.documentElement.classList.toggle('dark', initial === 'dark')
  }, [])

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    localStorage.setItem('emby-ui-theme', next)
    document.documentElement.classList.toggle('dark', next === 'dark')
  }

  return (
    <div className='min-h-screen bg-background'>
      <header className='sticky top-0 z-40 border-b bg-background/90 backdrop-blur'>
        <div className='mx-auto flex h-14 max-w-7xl items-center justify-between px-4 md:px-8'>
          <Link to='/' className='text-sm font-semibold tracking-wide text-primary'>
            EmbyIPLimit
          </Link>
          <nav className='hidden items-center gap-2 md:flex'>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 text-sm transition-colors ${
                    isActive ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <Button size='icon' variant='outline' onClick={toggleTheme} title='切换主题'>
            {theme === 'dark' ? <Sun className='h-4 w-4' /> : <Moon className='h-4 w-4' />}
          </Button>
        </div>
        <div className='mx-auto flex max-w-7xl gap-2 px-4 pb-3 md:hidden'>
          {navItems.map((item) => (
            <NavLink
              key={`mobile-${item.to}`}
              to={item.to}
              className={({ isActive }) =>
                `flex-1 rounded-md px-3 py-1.5 text-center text-sm transition-colors ${
                  isActive ? 'bg-primary text-primary-foreground' : 'bg-accent text-foreground'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </header>

      <main>
        {location.pathname !== '/' && location.pathname.startsWith('/admin') ? (
          <div className='mx-auto max-w-7xl px-4 pt-4 md:px-8'>
            <div className='mt-1 flex flex-wrap gap-2'>
              {adminSubNav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `rounded-md border px-3 py-1 text-sm transition-colors ${
                      isActive ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        ) : null}
        <Outlet />
      </main>
    </div>
  )
}
