// view_react/src/pages/Settings.jsx
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, UserPlus, Building2, Mail, Loader2, Key, Info, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'
import useAuthStore from '../store/authStore'
import { createAdmin, createOrganization } from '../api'
import clsx from 'clsx'

export default function Settings() {
  const { orgId, userName, role } = useAuthStore()
  const isSuperAdmin = role === 'super_admin'
  const [activeTab, setActiveTab] = useState('account')

  // Add-Admin form state
  const [adminForm, setAdminForm] = useState({ email: '', password: '', full_name: '', organization_id: '' })
  const [adminLoading, setAdminLoading] = useState(false)

  // Add-Organization form state
  const [orgForm, setOrgForm] = useState({ name: '', description: '' })
  const [orgLoading, setOrgLoading] = useState(false)

  const handleAdminField = (e) => setAdminForm(f => ({ ...f, [e.target.name]: e.target.value }))
  const handleOrgField = (e) => setOrgForm(f => ({ ...f, [e.target.name]: e.target.value }))

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

  const handleCreateOrganization = async (e) => {
    e.preventDefault()
    if (!orgForm.name) return toast.error('Organization name is required')
    
    setOrgLoading(true)
    try {
      const { data } = await createOrganization(orgForm)
      toast.success(`Organization "${data.name}" created with ID: ${data.id}`)
      setOrgForm({ name: '', description: '' })
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create organization')
    } finally {
      setOrgLoading(false)
    }
  }

  const TabButton = ({ id, label }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={clsx(
        'px-4 py-2 rounded-lg text-sm font-medium transition-all',
        activeTab === id ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-surface-800'
      )}
    >
      {label}
    </button>
  )

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle mt-1">Configure system preferences and manage access</p>
      </div>

      {/* Tabs Navigation */}
      <div className="flex gap-2 p-1 bg-surface-900 rounded-xl border border-surface-800 w-fit">
        <TabButton id="account" label="My Account" />
        {isSuperAdmin && (
          <>
            <TabButton id="organizations" label="Manage Organizations" />
            <TabButton id="admins" label="Manage Admins" />
          </>
        )}
      </div>

      {/* Tabs Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {/* ── ACCOUNT TAB ── */}
          {activeTab === 'account' && (
            <div className="space-y-6">
              <div className="card p-6 space-y-6">
                <div className="flex items-center gap-3 border-b border-surface-800 pb-4">
                  <Shield size={20} className="text-primary-400" />
                  <h2 className="font-semibold text-slate-200 text-lg">Profile Information</h2>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-surface-800/50 p-4 rounded-xl border border-surface-800 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-primary-600/20 flex items-center justify-center text-primary-400 text-xl font-bold">
                      {userName?.[0]?.toUpperCase()}
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 mb-0.5">Full Name</p>
                      <p className="font-medium text-slate-200">{userName}</p>
                    </div>
                  </div>
                  <div className="bg-surface-800/50 p-4 rounded-xl border border-surface-800 flex flex-col justify-center">
                    <p className="text-xs text-slate-500 mb-1">System Role</p>
                    <p className="font-medium text-emerald-400 capitalize">{role.replace('_', ' ')}</p>
                  </div>
                </div>
              </div>

              {/* System & Session Info (Useful for all admins) */}
              <div className="card p-6 space-y-4">
                <div className="flex items-center gap-3 border-b border-surface-800 pb-4">
                  <Info size={20} className="text-blue-400" />
                  <h2 className="font-semibold text-slate-200 text-lg">System Status</h2>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-800/30">
                    <CheckCircle2 size={18} className="text-emerald-400" />
                    <div>
                      <p className="text-sm font-medium text-slate-200">API Connection</p>
                      <p className="text-xs text-slate-500">Connected to backend services</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-800/30">
                    <Building2 size={18} className="text-slate-400" />
                    <div>
                      <p className="text-sm font-medium text-slate-200">Organization Scope</p>
                      <p className="text-xs text-slate-500">
                        {isSuperAdmin ? 'Global Access (All Organizations)' : `Restricted to Organization #${orgId}`}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── MANAGE ORGANIZATIONS TAB (Super Admin) ── */}
          {activeTab === 'organizations' && isSuperAdmin && (
            <div className="card p-6 space-y-6 border border-emerald-500/20">
              <div className="flex items-center justify-between border-b border-surface-800 pb-4">
                <div className="flex items-center gap-3">
                  <Building2 size={20} className="text-emerald-400" />
                  <h2 className="font-semibold text-slate-200 text-lg">Create Organization</h2>
                </div>
                <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Super Admin Only
                </span>
              </div>

              <p className="text-sm text-slate-400 mb-4">
                Create a new faculty, department, or organizational unit. Once created, you can assign an admin to manage it.
              </p>

              <form onSubmit={handleCreateOrganization} className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Organization Name</label>
                  <input name="name" value={orgForm.name} onChange={handleOrgField} placeholder="e.g. Faculty of Engineering" className="input" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Description (Optional)</label>
                  <textarea name="description" value={orgForm.description} onChange={handleOrgField} placeholder="Brief description of the faculty or unit..." className="input min-h-[100px] resize-y" />
                </div>
                
                <button type="submit" disabled={orgLoading} className="btn-primary w-full justify-center gap-2 py-2.5 mt-2 bg-emerald-600 hover:bg-emerald-500">
                  {orgLoading ? <><Loader2 size={16} className="animate-spin" /> Creating...</> : <><Building2 size={16} /> Create Organization</>}
                </button>
              </form>
            </div>
          )}

          {/* ── MANAGE ADMINS TAB (Super Admin) ── */}
          {activeTab === 'admins' && isSuperAdmin && (
            <div className="card p-6 space-y-6 border border-amber-500/20">
              <div className="flex items-center justify-between border-b border-surface-800 pb-4">
                <div className="flex items-center gap-3">
                  <UserPlus size={20} className="text-amber-400" />
                  <h2 className="font-semibold text-slate-200 text-lg">Create Admin Account</h2>
                </div>
                <span className="text-xs px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Super Admin Only
                </span>
              </div>

              <p className="text-sm text-slate-400 mb-4">
                Create a restricted administrator account. They will only be able to view and manage data for their assigned Organization ID.
              </p>

              <form onSubmit={handleCreateAdmin} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-slate-400 mb-1.5 block">Full Name</label>
                    <div className="relative">
                      <UserPlus size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                      <input name="full_name" value={adminForm.full_name} onChange={handleAdminField} placeholder="Dr. Ahmed Ali" className="input pl-10" />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-400 mb-1.5 block">Organization ID</label>
                    <div className="relative">
                      <Building2 size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                      <input name="organization_id" type="number" min={1} value={adminForm.organization_id} onChange={handleAdminField} placeholder="e.g. 1" className="input pl-10" />
                    </div>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Email Address</label>
                  <div className="relative">
                    <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input name="email" type="email" value={adminForm.email} onChange={handleAdminField} placeholder="admin@faculty.edu" className="input pl-10" />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Secure Password</label>
                  <div className="relative">
                    <Key size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input name="password" type="password" value={adminForm.password} onChange={handleAdminField} placeholder="Minimum 6 characters" className="input pl-10" />
                  </div>
                </div>
                <button type="submit" disabled={adminLoading} className="btn-primary w-full justify-center gap-2 py-2.5 mt-2">
                  {adminLoading ? <><Loader2 size={16} className="animate-spin" /> Creating Account...</> : <><UserPlus size={16} /> Create Administrator</>}
                </button>
              </form>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}