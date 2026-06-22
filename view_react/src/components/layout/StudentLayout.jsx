// view-react/src/components/layout/StudentLayout.jsx
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, CalendarDays, ClipboardList,
  GraduationCap, LogOut, MessageCircle, User,
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import clsx from 'clsx'

const nav = [
  { to: '/student/dashboard',  icon: LayoutDashboard, label: 'My Dashboard' },
  { to: '/student/attendance', icon: ClipboardList,   label: 'My Attendance' },
  { to: '/student/schedule',   icon: CalendarDays,    label: 'My Schedule' },
  { to: '/student/chat',       icon: MessageCircle,   label: 'AI Assistant' },
  { to: '/student/profile',    icon: User,            label: 'My Profile' },
]

export default function StudentLayout() {
  const { userName, logout } = useAuthStore()
  const navigate = useNavigate()

  return (
    <div className="flex h-screen overflow-hidden bg-surface-950">
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-64 h-screen flex flex-col bg-surface-900 border-r border-surface-800 fixed left-0 top-0 z-30"
      >
        {/* Logo */}
        <div className="p-6 border-b border-surface-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-emerald-600 rounded-xl flex items-center justify-center">
              <GraduationCap size={18} className="text-white" />
            </div>
            <div>
              <p className="font-bold text-slate-100 text-sm leading-none">SmartAttend</p>
              <p className="text-xs text-emerald-500 mt-0.5">Student Portal</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          <p className="section-label px-3 mb-3">Menu</p>
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) => clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'
              )}
            >
              {({ isActive }) => (
                <>
                  <Icon size={17} className={isActive ? 'text-emerald-400' : ''} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-surface-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-emerald-600/30 flex items-center justify-center text-emerald-400 font-semibold text-sm">
                {userName?.[0]?.toUpperCase() || 'S'}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-200 truncate">{userName || 'Student'}</p>
                <p className="text-xs text-emerald-600">Student</p>
              </div>
            </div>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
              title="Logout"
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </motion.aside>

      {/* Main content */}
      <main className="flex-1 ml-64 overflow-y-auto">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="min-h-full p-8"
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}