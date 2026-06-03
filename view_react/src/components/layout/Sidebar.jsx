// view-react/src/components/layout/Sidebar.jsx
import { NavLink, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, Users, Camera, BarChart3,
  MessageSquare, Settings, LogOut, GraduationCap,
  ChevronDown, BookOpen,
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import { useState } from 'react'
import clsx from 'clsx'

const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/students',  icon: Users,           label: 'Students' },
  { to: '/courses',   icon: BookOpen,        label: 'Courses' },
  { to: '/camera',    icon: Camera,          label: 'Camera' },
  { to: '/reports',   icon: BarChart3,       label: 'Reports' },
  { to: '/chat',      icon: MessageSquare,   label: 'AI Assistant' },
  { to: '/settings',  icon: Settings,        label: 'Settings' },
]

export default function Sidebar() {
  const { adminName, orgId, setOrgId, logout } = useAuthStore()
  const navigate = useNavigate()
  const [showOrgInput, setShowOrgInput] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-64 h-screen flex flex-col bg-surface-900 border-r border-surface-800 fixed left-0 top-0 z-30"
    >
      {/* Logo */}
      <div className="p-6 border-b border-surface-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center shadow-glow">
            <GraduationCap size={18} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-slate-100 text-sm leading-none">SmartAttend</p>
            <p className="text-xs text-slate-500 mt-0.5">AI Powered</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        <p className="section-label px-3 mb-3">Menu</p>
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
              isActive
                ? 'bg-primary-600/20 text-primary-400 border border-primary-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'
            )}
          >
            {({ isActive }) => (
              <>
                <Icon size={17} className={isActive ? 'text-primary-400' : ''} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Org Selector */}
      <div className="p-4 border-t border-surface-800">
        <button
          onClick={() => setShowOrgInput(!showOrgInput)}
          className="w-full flex items-center justify-between px-3 py-2 rounded-xl bg-surface-800 hover:bg-surface-700 transition-all text-sm text-slate-400"
        >
          <span>Org ID: <span className="text-slate-200 font-medium">{orgId}</span></span>
          <ChevronDown size={14} className={clsx('transition-transform', showOrgInput && 'rotate-180')} />
        </button>
        {showOrgInput && (
          <input
            type="number"
            min={1}
            value={orgId}
            onChange={(e) => setOrgId(Number(e.target.value))}
            className="input mt-2 text-sm"
            placeholder="Organization ID"
          />
        )}
      </div>

      {/* Admin */}
      <div className="p-4 border-t border-surface-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-600/30 flex items-center justify-center text-primary-400 font-semibold text-sm">
              {adminName?.[0]?.toUpperCase() || 'A'}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-200 truncate">{adminName || 'Admin'}</p>
              <p className="text-xs text-slate-500">Administrator</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
            title="Logout"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </motion.aside>
  )
}