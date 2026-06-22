// view-react/src/pages/student/StudentProfile.jsx
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  User, Mail, Hash, Building2, CalendarDays,
  TrendingUp, UserCheck, Clock, UserX, RefreshCw
} from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import { getMyProfile } from '../../api'

const InfoRow = ({ icon: Icon, label, value }) => (
  <div className="flex items-center gap-4 py-3 border-b border-surface-800 last:border-0">
    <div className="w-9 h-9 rounded-xl bg-surface-800 flex items-center justify-center flex-shrink-0">
      <Icon size={16} className="text-emerald-400" />
    </div>
    <div className="min-w-0">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-sm font-medium text-slate-200 truncate">{value}</p>
    </div>
  </div>
)

const StatPill = ({ icon: Icon, label, value, color }) => (
  <div className="flex items-center gap-3 bg-surface-800 rounded-xl p-4">
    <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
      <Icon size={16} />
    </div>
    <div>
      <p className="text-lg font-bold text-slate-100">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  </div>
)

export default function StudentProfile() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await getMyProfile()
      setProfile(data)
    } catch {
      toast.error('Failed to load your profile')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="h-8 w-48 bg-surface-800 rounded-xl animate-pulse" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-32 bg-surface-800 rounded-2xl animate-pulse" />)}
        </div>
      </div>
    )
  }

  if (!profile) return null

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">My Profile</h1>
          <p className="page-subtitle mt-1">Your personal and academic information</p>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Avatar + name card */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6 flex flex-col items-center text-center"
        >
          <div className="w-20 h-20 rounded-full bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-2xl font-bold text-emerald-400 mb-4">
            {profile.name?.[0]?.toUpperCase() || 'S'}
          </div>
          <p className="text-lg font-semibold text-slate-100">{profile.name}</p>
          <p className="text-sm text-emerald-500 mt-1">{profile.student_code}</p>

          <div className="w-full mt-6 pt-6 border-t border-surface-800">
            <p className="text-xs text-slate-500 mb-1">Attendance Rate</p>
            <p className={`text-3xl font-bold ${profile.attendance_percentage >= 75 ? 'text-emerald-400' : 'text-red-400'}`}>
              {profile.attendance_percentage}%
            </p>
          </div>
        </motion.div>

        {/* Personal info */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="card p-6 col-span-2"
        >
          <p className="font-semibold text-slate-200 mb-2">Personal Information</p>
          <InfoRow icon={User}        label="Full Name"      value={profile.name} />
          <InfoRow icon={Mail}        label="Email"           value={profile.email} />
          <InfoRow icon={Hash}        label="Student Code"    value={profile.student_code} />
          <InfoRow icon={Building2}   label="Organization"    value={profile.organization_name} />
          <InfoRow icon={CalendarDays} label="Enrollment Date" value={format(new Date(profile.enrollment_date), 'MMMM d, yyyy')} />
        </motion.div>
      </div>

      {/* Attendance summary */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card p-6"
      >
        <p className="font-semibold text-slate-200 mb-4">Attendance Summary</p>
        <div className="grid grid-cols-4 gap-4">
          <StatPill icon={TrendingUp} label="Attendance Rate" value={`${profile.attendance_percentage}%`} color="bg-primary-500/20 text-primary-400" />
          <StatPill icon={UserCheck}  label="Present Days"    value={profile.present_days}                color="bg-emerald-500/20 text-emerald-400" />
          <StatPill icon={Clock}      label="Late Arrivals"   value={profile.late_days}                   color="bg-amber-500/20 text-amber-400" />
          <StatPill icon={UserX}      label="Absent Days"     value={profile.absent_days}                 color="bg-red-500/20 text-red-400" />
        </div>
      </motion.div>
    </div>
  )
}