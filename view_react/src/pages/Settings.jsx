// view_react/src/pages/Settings.jsx
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Settings as SettingsIcon, Building2, Clock, Shield, Info, UserPlus } from 'lucide-react'
import useAuthStore from '../store/authStore'
import { createAdmin } from '../api'
import toast from 'react-hot-toast'

export default function Settings() {
  const { orgId, userName, role } = useAuthStore()
  const isSuperAdmin = role === 'super_admin'

  // ... existing state (sessionHour, sessionMinute, lateThreshold) unchanged ...

  // Add-admin form state
  const [adminForm, setAdminForm] = useState({ email: '', password: '', full_name: '', organization_id: '' })
  const [adminLoading, setAdminLoading] = useState(false)

  const handleAdminField = (e) => setAdminForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleCreateAdmin = async (e) => {
    e.preventDefault()
    if (!adminForm.email || !adminForm.password || !adminForm.full_name || !adminForm.organization_id)
      return toast.error('All fields are required')
    if (adminForm.password.length < 6) return toast.error('Password must be at least 6 characters')
    setAdminLoading(true)
    try {
      await createAdmin({ ...adminForm, role: 'admin', organization_id: Number(adminForm.organization_id) })
      toast.success(`Admin account created for ${adminForm.email}`)
      setAdminForm({ email: '', password: '', full_name: '', organization_id: '' })
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create admin')
    } finally {
      setAdminLoading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle mt-1">Configure your system preferences</p>
      </div>

      {/* Account card */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Shield size={16} className="text-primary-400" />
          <h2 className="font-semibold text-slate-200">Account</h2>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary-600/20 flex items-center justify-center text-primary-400 font-bold text-lg">
            {userName?.[0]?.toUpperCase() || 'A'}
          </div>
          <div>
            <p className="font-medium text-slate-200">{userName}</p>
            <p className="text-sm text-slate-500">
              {role === 'super_admin' ? 'Super Administrator' : 'Administrator'}
              {orgId && <span className="ml-2 text-slate-600">· Org #{orgId}</span>}
            </p>
          </div>
        </div>
      </div>

      {/* ... existing Session Timing and API Info cards unchanged ... */}

      {/* Add Admin — super_admin only */}
      {isSuperAdmin && (
        <div className="card p-6 space-y-4 border border-amber-500/20">
          <div className="flex items-center gap-3">
            <UserPlus size={16} className="text-amber-400" />
            <h2 className="font-semibold text-slate-200">Create Admin Account</h2>
            <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Super Admin Only
            </span>
          </div>

          <form onSubmit={handleCreateAdmin} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-400 mb-1.5 block">Full Name</label>
                <input
                  name="full_name" value={adminForm.full_name} onChange={handleAdminField}
                  placeholder="Dr. Ahmed Ali" className="input"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-400 mb-1.5 block">Organization ID</label>
                <input
                  name="organization_id" type="number" min={1}
                  value={adminForm.organization_id} onChange={handleAdminField}
                  placeholder="1" className="input"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400 mb-1.5 block">Email</label>
              <input
                name="email" type="email" value={adminForm.email} onChange={handleAdminField}
                placeholder="admin@faculty.edu" className="input"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400 mb-1.5 block">Password</label>
              <input
                name="password" type="password" value={adminForm.password} onChange={handleAdminField}
                placeholder="min 6 characters" className="input"
              />
            </div>
            <button
              type="submit" disabled={adminLoading}
              className="btn-primary text-sm flex items-center gap-2"
            >
              {adminLoading
                ? <><span className="animate-spin">⏳</span> Creating...</>
                : <><UserPlus size={14} /> Create Admin</>
              }
            </button>
          </form>
        </div>
      )}
    </div>
  )
}