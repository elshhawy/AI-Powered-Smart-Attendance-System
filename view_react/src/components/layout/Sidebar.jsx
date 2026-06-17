// view_react/src/components/layout/Sidebar.jsx
import { NavLink, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, Users, Camera, BarChart3,
  MessageSquare, Settings, LogOut, GraduationCap,
  BookOpen, ShieldCheck,
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import clsx from 'clsx'

// nav items + which roles can see them
const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard',    roles: ['admin', 'super_admin'] },
  { to: '/students',  icon: Users,           label: 'Students',     roles: ['admin', 'super_admin'] },
  { to: '/courses',   icon: BookOpen,        label: 'Courses',      roles: ['admin', 'super_admin'] },
  { to: '/camera',    icon: Camera,          label: 'Camera',       roles: ['admin', 'super_admin'] },
  { to: '/reports',   icon: BarChart3,       label: 'Reports',      roles: ['admin', 'super_admin'] },
  { to: '/chat',      icon: MessageSquare,   label: 'AI Assistant', roles: ['admin', 'super_admin'] },
  { to: '/settings',  icon: Settings,        label: 'Settings',     roles: ['admin', 'super_admin'] },
]

export default function Sidebar() {
  const { userName, role, orgId, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  const visibleNav = nav.filter(item => item.roles.includes(role))

  const roleLabel = role === 'super_admin' ? 'Super Admin'
                  : role === 'admin'       ? 'Administrator'
                  : 'User'

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
        {visibleNav.map(({ to, icon: Icon, label }) => (
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

        {/* Super-admin-only section */}
        {role === 'super_admin' && (
          <>
            <p className="section-label px-3 mt-4 mb-3">Super Admin</p>
            <NavLink
              to="/settings/add-admin"
              className={({ isActive }) => clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-amber-600/20 text-amber-400 border border-amber-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'
              )}
            >
              {({ isActive }) => (
                <>
                  <ShieldCheck size={17} className={isActive ? 'text-amber-400' : ''} />
                  Add Admin
                </>
              )}
            </NavLink>
          </>
        )}
      </nav>

      {/* Org badge — read-only, sourced from token */}
      {orgId && (
        <div className="px-4 py-2 border-t border-surface-800">
          <p className="text-xs text-slate-500">
            Organization: <span className="text-slate-300 font-medium">#{orgId}</span>
          </p>
        </div>
      )}

      {/* User footer */}
      <div className="p-4 border-t border-surface-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-600/30 flex items-center justify-center text-primary-400 font-semibold text-sm">
              {userName?.[0]?.toUpperCase() || 'A'}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-200 truncate">{userName || 'User'}</p>
              <p className="text-xs text-slate-500">{roleLabel}</p>
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