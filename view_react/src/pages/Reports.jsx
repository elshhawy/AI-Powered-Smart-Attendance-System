import { useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, Download, Search, TrendingUp, AlertTriangle } from 'lucide-react'
import { format, subDays } from 'date-fns'
import toast from 'react-hot-toast'
import { getAttendanceRange, getStudentStats } from '../api'
import useAuthStore from '../store/authStore'

export default function Reports() {
  const [tab, setTab] = useState('range')
  const { orgId } = useAuthStore()

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">Reports</h1>
        <p className="page-subtitle mt-1">Attendance analytics and exports</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1 bg-surface-900 rounded-xl border border-surface-800 w-fit">
        {[['range','Date Range'],['stats','Student Stats']].map(([t, l]) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              tab === t ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >{l}</button>
        ))}
      </div>

      {tab === 'range' ? <RangeReport orgId={orgId} /> : <StatsReport />}
    </div>
  )
}

function RangeReport({ orgId }) {
  const [start, setStart] = useState(format(subDays(new Date(), 7), 'yyyy-MM-dd'))
  const [end, setEnd] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await getAttendanceRange(orgId, start, end)
      setRecords(data.records || [])
      setSearched(true)
    } catch { toast.error('Failed to load records') }
    finally { setLoading(false) }
  }

  const downloadCSV = () => {
    const headers = 'Student ID,Date,Status,Late,Confidence\n'
    const rows = records.map(r => `${r.student_id},${r.date},${r.status},${r.is_late},${r.confidence ?? ''}`).join('\n')
    const blob = new Blob([headers + rows], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
    a.download = `attendance_${start}_${end}.csv`; a.click()
  }

  return (
    <div className="space-y-4">
      <div className="card p-6 flex gap-4 items-end">
        <div className="flex-1">
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">From</label>
          <input type="date" className="input" value={start} onChange={e => setStart(e.target.value)} />
        </div>
        <div className="flex-1">
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">To</label>
          <input type="date" className="input" value={end} onChange={e => setEnd(e.target.value)} />
        </div>
        <button onClick={load} disabled={loading} className="btn-primary flex items-center gap-2">
          <Search size={15} /> Generate
        </button>
        {records.length > 0 && (
          <button onClick={downloadCSV} className="btn-secondary flex items-center gap-2">
            <Download size={15} /> CSV
          </button>
        )}
      </div>

      {loading ? (
        <div className="card p-8 space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-10 bg-surface-800 rounded-xl animate-pulse" />)}
        </div>
      ) : searched && records.length === 0 ? (
        <div className="card py-16 text-center">
          <BarChart3 size={40} className="text-slate-700 mx-auto mb-3" />
          <p className="text-slate-500">No records for this period</p>
        </div>
      ) : records.length > 0 ? (
        <div className="card overflow-hidden">
          <div className="px-6 py-4 border-b border-surface-800 flex items-center justify-between">
            <p className="font-semibold text-slate-200">{records.length} records</p>
          </div>
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
                      <span className={r.status === 'present' ? 'badge-present' : 'badge-absent'}>{r.status}</span>
                    </td>
                    <td className="px-6 py-3">
                      {r.is_late ? <span className="badge-late">Late</span> : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-6 py-3 text-slate-400">{r.confidence ? `${Math.round(r.confidence * 100)}%` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  )
}

function StatsReport() {
  const [studentId, setStudentId] = useState('')
  const [start, setStart] = useState(format(subDays(new Date(), 30), 'yyyy-MM-dd'))
  const [end, setEnd] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    if (!studentId) return toast.error('Enter a student ID')
    setLoading(true)
    try {
      const { data } = await getStudentStats(studentId, start, end)
      setStats(data)
    } catch { toast.error('Student not found') }
    finally { setLoading(false) }
  }

  return (
    <div className="space-y-4">
      <div className="card p-6 flex gap-4 items-end">
        <div>
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">Student ID</label>
          <input className="input w-32" placeholder="1" value={studentId} onChange={e => setStudentId(e.target.value)} />
        </div>
        <div className="flex-1">
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">From</label>
          <input type="date" className="input" value={start} onChange={e => setStart(e.target.value)} />
        </div>
        <div className="flex-1">
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">To</label>
          <input type="date" className="input" value={end} onChange={e => setEnd(e.target.value)} />
        </div>
        <button onClick={load} disabled={loading} className="btn-primary flex items-center gap-2">
          <Search size={15} /> Search
        </button>
      </div>

      {stats && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Attendance Rate', value: `${stats.attendance_percentage}%`, color: 'text-primary-400' },
              { label: 'Total Days',      value: stats.total_days,                  color: 'text-slate-200' },
              { label: 'Present Days',    value: stats.present_days,                color: 'text-emerald-400' },
              { label: 'Late Days',       value: stats.late_days,                   color: 'text-amber-400' },
            ].map(({ label, value, color }) => (
              <div key={label} className="stat-card">
                <p className={`text-3xl font-bold ${color}`}>{value}</p>
                <p className="text-sm text-slate-500">{label}</p>
              </div>
            ))}
          </div>

          {stats.attendance_percentage < 75 && (
            <div className="card p-4 border-red-500/20 bg-red-500/5 flex items-center gap-3">
              <AlertTriangle size={18} className="text-red-400 flex-shrink-0" />
              <p className="text-sm text-red-300">This student is at risk — attendance is below 75%</p>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
