import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Users, UserCheck, Clock, UserX, TrendingUp, RefreshCw, CheckCircle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import { getTodayAttendance, listStudents, markAbsents } from '../api'
import useAuthStore from '../store/authStore'

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

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card px-3 py-2 text-sm">
      <p className="text-slate-400">{label}</p>
      <p className="text-slate-100 font-semibold">{payload[0].value} students</p>
    </div>
  )
}

export default function Dashboard() {
  const [records, setRecords] = useState([])
  const [totalStudents, setTotalStudents] = useState(0)
  const [loading, setLoading] = useState(true)
  const [marking, setMarking] = useState(false)
  const { orgId } = useAuthStore()

  const load = async () => {
    setLoading(true)
    try {
      const [att, stu] = await Promise.all([
        getTodayAttendance(orgId),
        listStudents(orgId),
      ])
      setRecords(att.data.records || [])
      setTotalStudents(stu.data.total || 0)
    } catch {
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [orgId])

  const present = records.filter(r => r.status === 'present' && !r.is_late).length
  const late    = records.filter(r => r.is_late).length
  const absent  = totalStudents - present - late
  const rate    = totalStudents ? Math.round((present + late) / totalStudents * 100) : 0

  const chartData = [
    { name: 'Present', value: present, color: '#10b981' },
    { name: 'Late',    value: late,    color: '#f59e0b' },
    { name: 'Absent',  value: absent,  color: '#ef4444' },
  ]

  const handleMarkAbsent = async () => {
    setMarking(true)
    try {
      const { data } = await markAbsents(orgId)
      toast.success(`${data.marked_count} students marked absent`)
      load()
    } catch {
      toast.error('Failed to mark absents')
    } finally {
      setMarking(false)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle mt-1">{format(new Date(), 'EEEE, MMMM d, yyyy')}</p>
        </div>
        <div className="flex gap-3">
          <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm">
            <RefreshCw size={14} /> Refresh
          </button>
          <button onClick={handleMarkAbsent} disabled={marking} className="btn-primary flex items-center gap-2 text-sm">
            <CheckCircle size={14} />
            {marking ? 'Marking...' : 'Mark Absents'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard icon={Users}     label="Total Students" value={totalStudents} color="bg-primary-500/20 text-primary-400"  delay={0} />
        <StatCard icon={UserCheck} label="Present"        value={present}       color="bg-emerald-500/20 text-emerald-400" delay={0.05} />
        <StatCard icon={Clock}     label="Late"           value={late}          color="bg-amber-500/20 text-amber-400"     delay={0.1} />
        <StatCard icon={UserX}     label="Absent"         value={absent}        color="bg-red-500/20 text-red-400"         delay={0.15} />
      </div>

      {/* Chart + Rate */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-6 col-span-2">
          <p className="font-semibold text-slate-200 mb-4">Today's Breakdown</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} barSize={40}>
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 13 }} />
              <YAxis hide />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,.04)' }} />
              <Bar dataKey="value" radius={[8,8,0,0]}>
                {chartData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6 flex flex-col items-center justify-center gap-3">
          <div className="relative w-28 h-28">
            <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#1e293b" strokeWidth="10" />
              <circle cx="50" cy="50" r="40" fill="none" stroke="#6172f3" strokeWidth="10"
                strokeDasharray={`${2.51 * rate} ${251 - 2.51 * rate}`}
                strokeLinecap="round" className="transition-all duration-700" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-slate-100">{rate}%</span>
            </div>
          </div>
          <div className="text-center">
            <p className="font-semibold text-slate-200">Attendance Rate</p>
            <p className="text-xs text-slate-500 mt-0.5">Today's overview</p>
          </div>
          <div className="flex items-center gap-1 text-xs text-emerald-400">
            <TrendingUp size={12} /> On track
          </div>
        </div>
      </div>

      {/* Records Table */}
      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-surface-800">
          <p className="font-semibold text-slate-200">Attendance Records</p>
          <p className="text-xs text-slate-500 mt-0.5">{records.length} entries today</p>
        </div>

        {loading ? (
          <div className="p-8 space-y-3">
            {[1,2,3].map(i => (
              <div key={i} className="h-10 bg-surface-800 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : records.length === 0 ? (
          <div className="py-16 text-center">
            <UserCheck size={40} className="text-slate-700 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No records yet</p>
            <p className="text-sm text-slate-600 mt-1">Use the Camera page to record attendance</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-800">
                  {['Student ID','Date','Status','Late','Confidence'].map(h => (
                    <th key={h} className="text-left px-6 py-3 text-xs font-medium text-slate-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.map((r, i) => (
                  <tr key={i} className="border-b border-surface-800/50 hover:bg-surface-800/30 transition-colors">
                    <td className="px-6 py-3 text-slate-300 font-medium">#{r.student_id}</td>
                    <td className="px-6 py-3 text-slate-400">{r.date}</td>
                    <td className="px-6 py-3">
                      <span className={r.status === 'present' ? 'badge-present' : 'badge-absent'}>
                        {r.status}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      {r.is_late ? <span className="badge-late">Late</span> : <span className="text-slate-500">—</span>}
                    </td>
                    <td className="px-6 py-3 text-slate-400">
                      {r.confidence ? `${Math.round(r.confidence * 100)}%` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
