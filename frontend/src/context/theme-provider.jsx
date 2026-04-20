import { createContext, useContext, useEffect, useState, useMemo } from 'react'

const DEFAULT_THEME = 'system'
const THEME_STORAGE_KEY = 'emby-ui-theme'

const ThemeContext = createContext(null)

export function ThemeProvider({ children, defaultTheme = DEFAULT_THEME, storageKey = THEME_STORAGE_KEY, ...props }) {
  const [theme, _setTheme] = useState(() => localStorage.getItem(storageKey) || defaultTheme)

  const resolvedTheme = useMemo(() => {
    if (theme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return theme
  }, [theme])

  useEffect(() => {
    const root = window.document.documentElement
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const applyTheme = (currentResolvedTheme) => {
      root.classList.remove('light', 'dark')
      root.classList.add(currentResolvedTheme)
    }

    const handleChange = () => {
      if (theme === 'system') {
        const systemTheme = mediaQuery.matches ? 'dark' : 'light'
        applyTheme(systemTheme)
      }
    }

    applyTheme(resolvedTheme)
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [theme, resolvedTheme])

  const setTheme = (newTheme) => {
    localStorage.setItem(storageKey, newTheme)
    _setTheme(newTheme)
  }

  return (
    <ThemeContext value={{ theme, resolvedTheme, setTheme }} {...props}>
      {children}
    </ThemeContext>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within a ThemeProvider')
  return context
}
