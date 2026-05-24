import { NavLink } from 'react-router-dom'
import { FileText, Brain, Settings, BookOpen, Moon, Sun, ChevronLeft, ChevronRight } from 'lucide-react'
import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Dokumentbibliotek', icon: FileText, exact: true },
  { to: '/memory', label: 'Hukommelse', icon: Brain },
  { to: '/settings', label: 'Innstillinger', icon: Settings },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const [dark, setDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark' ||
        (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
    }
    return false
  })

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [dark])

  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-hoyre-blue dark:bg-gray-900 text-white transition-all duration-300 flex-shrink-0',
        collapsed ? 'w-16' : 'w-56',
      )}
    >
      {/* Logo */}
      <div className={cn('flex items-center gap-3 px-4 py-5 border-b border-white/10', collapsed && 'justify-center px-2')}>
        <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center flex-shrink-0">
          <BookOpen size={16} className="text-hoyre-blue" />
        </div>
        {!collapsed && (
          <div>
            <div className="font-semibold text-sm leading-tight">Politikerapp</div>
            <div className="text-xs text-white/60">Høyre</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map(({ to, label, icon: Icon, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                collapsed && 'justify-center px-2',
                isActive
                  ? 'bg-white/20 text-white'
                  : 'text-white/70 hover:bg-white/10 hover:text-white',
              )
            }
            title={collapsed ? label : undefined}
          >
            <Icon size={18} className="flex-shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom controls */}
      <div className="p-2 border-t border-white/10 space-y-1">
        <button
          onClick={() => setDark(!dark)}
          className="btn-ghost w-full text-white/70 hover:text-white hover:bg-white/10 justify-center"
          title={dark ? 'Lys modus' : 'Mørk modus'}
        >
          {dark ? <Sun size={18} /> : <Moon size={18} />}
          {!collapsed && <span className="ml-2 text-xs">{dark ? 'Lys' : 'Mørk'}</span>}
        </button>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="btn-ghost w-full text-white/70 hover:text-white hover:bg-white/10 justify-center"
          title={collapsed ? 'Utvid sidepanel' : 'Minimer sidepanel'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          {!collapsed && <span className="ml-2 text-xs">Minimer</span>}
        </button>
      </div>
    </aside>
  )
}
