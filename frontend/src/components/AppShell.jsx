import { useEffect, useMemo, useState } from 'react'
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

  const title = useMemo(() => {
    if (location.pathname.startsWith('/admin/groups')) return '用户组管理'
    if (location.pathname.startsWith('/admin/config')) return '配置管理'
    if (location.pathname.startsWith('/admin/users')) return '用户管理'
    if (location.pathname.startsWith('/admin')) return '管理后台'
    if (location.pathname.startsWith('/search')) return '用户查询'
    return 'Emby IPLimit'
  }, [location.pathname])

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
      </header>

      <main>
        <div className='mx-auto max-w-7xl px-4 pt-4 md:px-8'>
          <h2 className='text-lg font-semibold'>{title}</h2>
          {location.pathname.startsWith('/admin') ? (
            <div className='mt-3 flex flex-wrap gap-2'>
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
          ) : null}
        </div>
        <Outlet />
      </main>
    </div>
  )
}
