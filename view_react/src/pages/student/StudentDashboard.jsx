// view-react/src/pages/student/StudentDashboard.jsx
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  UserCheck, Clock, UserX, TrendingUp,
  AlertTriangle, BookOpen, RefreshCw
} from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { getMyProfile, getMyStatistics } from '../../api'

const StatCard = ({ icon: Icon, label, value, color, delay }) => (
  <motion.div
    initial={{ opacity: 0, y: 16 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    className="stat-card"
  >
    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
      <Icon size={18} />
    </div>
    <div>
      <p className="text-3xl font-bold text-slate-100">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  </motion.div>
)

const COLORS = ['#10b981', '#f59e0b', '#ef4444']

export default function StudentDashboard() {
  const [profile, setProfile]   = useState(null)
  const [stats, setStats]       = useState(null)
  const [loading, setLoading]   = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [profileRes, statsRes] = await Promise.all([
        getMyProfile(),
        getMyStatistics(30),
      ])
      setProfile(profileRes.data)
      setStats(statsRes.data)
    } catch (e) {
      toast.error('Failed to load your data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="h-8 w-48 bg-surface-800 rounded-xl animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="h-32 bg-surface-800 rounded-2xl animate-pulse" />)}
        </div>
      </div>
    )
  }

  if (!profile) return null

  const chartData = [
    { name: 'Present', value: profile.present_days },
    { name: 'Late',    value: profile.late_days },
    { name: 'Absent',  value: profile.absent_days },
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Welcome, {profile.name.split(' ')[0]} 👋</h1>
          <p className="page-subtitle mt-1">{format(new Date(), 'EEEE, MMMM d, yyyy')}</p>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* At-risk warning */}
      {profile.attendance_percentage < 75 && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-4 border-red-500/20 bg-red-500/5 flex items-center gap-3"
        >
          <AlertTriangle size={20} className="text-red-400 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-300">⚠️ Low Attendance Alert</p>
            <p className="text-xs text-slate-500 mt-0.5">
              Your attendance is {profile.attendance_percentage}% — below the required 75%.
              Please attend your classes regularly.
            </p>
          </div>
        </motion.div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard icon={TrendingUp} label="Attendance Rate"  value={`${profile.attendance_percentage}%`} color="bg-primary-500/20 text-primary-400"  delay={0} />
        <StatCard icon={UserCheck}  label="Present Days"     value={profile.present_days}                color="bg-emerald-500/20 text-emerald-400" delay={0.05} />
        <StatCard icon={Clock}      label="Late Arrivals"    value={profile.late_days}                   color="bg-amber-500/20 text-amber-400"     delay={0.1} />
        <StatCard icon={UserX}      label="Absent Days"      value={profile.absent_days}                 color="bg-red-500/20 text-red-400"         delay={0.15} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-3 gap-4">
        {/* Pie Chart */}
        <div className="card p-6 flex flex-col items-center justify-center gap-4">
          <p className="font-semibold text-slate-200 self-start">Overall Breakdown</p>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={chartData} cx="50%" cy="50%" innerRadius={50} outerRadius={75}
                dataKey="value" paddingAngle={3}>
                {chartData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }}
                labelStyle={{ color: '#94a3b8' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex gap-4 text-xs">
            {[['Present','#10b981'], ['Late','#f59e0b'], ['Absent','#ef4444']].map(([l, c]) => (
              <div key={l} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: c }} />
                <span className="text-slate-400">{l}</span>
              </div>
            ))}
          </div>
        </div>

        {/* By Course */}
        <div className="card p-6 col-span-2">
          <p className="font-semibold text-slate-200 mb-4">By Course (Last 30 days)</p>
          {stats && Object.keys(stats.by_course).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(stats.by_course).map(([course, data]) => {
                const pct = data.total ? Math.round((data.present + data.late) / data.total * 100) : 0
                return (
                  <div key={course}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <BookOpen size={13} className="text-slate-500" />
                        <span className="text-sm text-slate-300">{course}</span>
                      </div>
                      <span className={`text-sm font-medium ${pct >= 75 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {pct}%
                      </span>
                    </div>
                    <div className="h-1.5 bg-surface-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${pct >= 75 ? 'bg-emerald-500' : 'bg-red-500'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500 text-sm">
              No course data yet
            </div>
          )}
        </div>
      </div>

      {/* Student Info */}
      <div className="card p-6">
        <p className="font-semibold text-slate-200 mb-4">My Info</p>
        <div className="grid grid-cols-3 gap-4 text-sm">
          {[
            ['Student Code',    profile.student_code],
            ['Enrolled',        profile.enrollment_date],
            ['Total Records',   profile.total_days],
          ].map(([label, value]) => (
            <div key={label} className="bg-surface-800 rounded-xl p-4">
              <p className="text-slate-500 text-xs mb-1">{label}</p>
              <p className="text-slate-200 font-medium">{value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}