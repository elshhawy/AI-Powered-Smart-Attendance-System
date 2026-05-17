import { useState } from 'react'
import { motion } from 'framer-motion'
import { Settings as SettingsIcon, Building2, Clock, Shield, Info } from 'lucide-react'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'

export default function Settings() {
  const { orgId, setOrgId, adminName } = useAuthStore()
  const [localOrgId, setLocalOrgId] = useState(orgId)
  const [sessionHour, setSessionHour] = useState(9)
  const [sessionMinute, setSessionMinute] = useState(0)
  const [lateThreshold, setLateThreshold] = useState(15)

  const saveOrg = () => {
    setOrgId(Number(localOrgId))
    toast.success('Organization updated')
  }

  const saveSession = () => {
    toast.success('Session settings saved (requires .env update for persistence)')
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle mt-1">Configure your system preferences</p>
      </div>

      {/* Admin Info */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Shield size={16} className="text-primary-400" />
          <h2 className="font-semibold text-slate-200">Account</h2>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary-600/20 flex items-center justify-center text-primary-400 font-bold text-lg">
            {adminName?.[0]?.toUpperCase() || 'A'}
          </div>
          <div>
            <p className="font-medium text-slate-200">{adminName}</p>
            <p className="text-sm text-slate-500">Administrator</p>
          </div>
        </div>
      </div>

      {/* Organization */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-3">
          <Building2 size={16} className="text-primary-400" />
          <h2 className="font-semibold text-slate-200">Organization</h2>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">Organization ID</label>
          <div className="flex gap-3">
            <input
              type="number" min={1}
              className="input w-32"
              value={localOrgId}
              onChange={e => setLocalOrgId(e.target.value)}
            />
            <button onClick={saveOrg} className="btn-primary text-sm">Save</button>
          </div>
          <p className="text-xs text-slate-600 mt-2">This sets which organization's data you're viewing across all pages.</p>
        </div>
      </div>

      {/* Session Timing */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-3">
          <Clock size={16} className="text-primary-400" />
          <h2 className="font-semibold text-slate-200">Session Timing</h2>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Start Hour</label>
            <input type="number" min={0} max={23} className="input" value={sessionHour} onChange={e => setSessionHour(e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Start Minute</label>
            <input type="number" min={0} max={59} className="input" value={sessionMinute} onChange={e => setSessionMinute(e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Late After (min)</label>
            <input type="number" min={1} className="input" value={lateThreshold} onChange={e => setLateThreshold(e.target.value)} />
          </div>
        </div>
        <div className="flex items-start gap-2 p-3 rounded-xl bg-surface-800 border border-surface-700">
          <Info size={14} className="text-slate-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-slate-500">
            Session starts at <span className="text-slate-300">{String(sessionHour).padStart(2,'0')}:{String(sessionMinute).padStart(2,'0')}</span>.
            Students arriving after <span className="text-slate-300">{lateThreshold} minutes</span> are marked late.
            To persist these values, update your <span className="text-slate-300">.env</span> file.
          </p>
        </div>
        <button onClick={saveSession} className="btn-primary text-sm">Save Settings</button>
      </div>

      {/* API Info */}
      <div className="card p-6 space-y-3">
        <div className="flex items-center gap-3">
          <Info size={16} className="text-primary-400" />
          <h2 className="font-semibold text-slate-200">API</h2>
        </div>
        <div className="space-y-2 text-sm">
          {[
            ['Backend URL', 'http://localhost:8000'],
            ['Swagger Docs', 'http://localhost:8000/docs'],
            ['Frontend URL', 'http://localhost:3000'],
          ].map(([label, value]) => (
            <div key={label} className="flex items-center justify-between py-2 border-b border-surface-800 last:border-0">
              <span className="text-slate-500">{label}</span>
              <a href={value} target="_blank" rel="noreferrer" className="text-primary-400 hover:underline font-mono text-xs">{value}</a>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
