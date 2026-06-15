// view-react/src/pages/student/StudentAttendance.jsx
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ClipboardList, Filter } from 'lucide-react'
import toast from 'react-hot-toast'
import { getMyAttendance } from '../../api'

export default function StudentAttendance() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [days, setDays]       = useState(30)
  const [filter, setFilter]   = useState('all') // all | present | late | absent

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await getMyAttendance(days)
      setRecords(data)
    } catch { toast.error('Failed to load attendance') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [days])

  const filtered = records.filter(r => {
    if (filter === 'all')     return true
    if (filter === 'late')    return r.is_late
    if (filter === 'absent')  return r.status === 'absent'
    if (filter === 'present') return r.status === 'present' && !r.is_late
    return true
  })

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">My Attendance</h1>
          <p className="page-subtitle mt-1">{records.length} records</p>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          <select
            className="input text-sm w-36"
            value={days}
            onChange={e => setDays(Number(e.target.value))}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>This year</option>
          </select>
        </div>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 p-1 bg-surface-900 rounded-xl border border-surface-800 w-fit">
        {[['all','All'],['present','Present'],['late','Late'],['absent','Absent']].map(([v,l]) => (
          <button key={v} onClick={() => setFilter(v)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              filter === v ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >{l}</button>
        ))}
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-3">
            {[1,2,3,4,5].map(i => <div key={i} className="h-12 bg-surface-800 rounded-xl animate-pulse" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center">
            <ClipboardList size={48} className="text-slate-700 mx-auto mb-3" />
            <p className="text-slate-400 font-medium">No records found</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-800">
                {['Date', 'Course', 'Type', 'Status', 'Arrived'].map(h => (
                  <th key={h} className="text-left px-6 py-3 text-xs font-medium text-slate-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((r, i) => (
                <motion.tr key={r.id}
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                  className="border-b border-surface-800/50 hover:bg-surface-800/30 transition-colors"
                >
                  <td className="px-6 py-3 text-slate-300 font-medium">{r.date}</td>
                  <td className="px-6 py-3 text-slate-400">{r.course_name || '—'}</td>
                  <td className="px-6 py-3 text-slate-500 capitalize">{r.session_type || '—'}</td>
                  <td className="px-6 py-3">
                    {r.status === 'absent' ? (
                      <span className="badge-absent">Absent</span>
                    ) : r.is_late ? (
                      <span className="badge-late">Late</span>
                    ) : (
                      <span className="badge-present">Present</span>
                    )}
                  </td>
                  <td className="px-6 py-3 text-slate-500">
                    {r.confidence ? `${Math.round(r.confidence * 100)}% confidence` : '—'}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}