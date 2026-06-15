// view-react/src/pages/student/StudentSchedule.jsx
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { CalendarDays, Clock } from 'lucide-react'
import toast from 'react-hot-toast'
import { getMySchedule } from '../../api'

const DAY_COLORS = {
  Monday:    'bg-blue-500/15 text-blue-400 border-blue-500/20',
  Tuesday:   'bg-purple-500/15 text-purple-400 border-purple-500/20',
  Wednesday: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  Thursday:  'bg-amber-500/15 text-amber-400 border-amber-500/20',
  Friday:    'bg-rose-500/15 text-rose-400 border-rose-500/20',
  Saturday:  'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
  Sunday:    'bg-slate-500/15 text-slate-400 border-slate-500/20',
}

const SESSION_COLORS = {
  lecture:  'bg-blue-500/15 text-blue-400',
  section:  'bg-emerald-500/15 text-emerald-400',
  lab:      'bg-purple-500/15 text-purple-400',
  tutorial: 'bg-amber-500/15 text-amber-400',
  exam:     'bg-red-500/15 text-red-400',
}

const DAYS_ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

export default function StudentSchedule() {
  const [schedule, setSchedule] = useState([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await getMySchedule()
        setSchedule(data)
      } catch { toast.error('Failed to load schedule') }
      finally { setLoading(false) }
    }
    load()
  }, [])

  // Group by day
  const byDay = DAYS_ORDER.reduce((acc, day) => {
    const sessions = schedule.filter(s => s.day_name === day)
    if (sessions.length > 0) acc[day] = sessions
    return acc
  }, {})

  if (loading) {
    return (
      <div className="space-y-4 animate-fade-in">
        <div className="h-8 w-48 bg-surface-800 rounded-xl animate-pulse" />
        {[1,2,3].map(i => <div key={i} className="h-32 bg-surface-800 rounded-2xl animate-pulse" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">My Schedule</h1>
        <p className="page-subtitle mt-1">Weekly timetable for all your courses</p>
      </div>

      {Object.keys(byDay).length === 0 ? (
        <div className="card py-20 text-center">
          <CalendarDays size={48} className="text-slate-700 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">No schedule yet</p>
          <p className="text-sm text-slate-600 mt-1">Your admin hasn't added any sessions</p>
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(byDay).map(([day, sessions], di) => (
            <motion.div key={day}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: di * 0.05 }}
              className="card overflow-hidden"
            >
              {/* Day header */}
              <div className="px-5 py-3 border-b border-surface-800 flex items-center gap-3">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${DAY_COLORS[day] || 'bg-slate-500/15 text-slate-400'}`}>
                  {day}
                </span>
                <span className="text-xs text-slate-500">{sessions.length} session{sessions.length > 1 ? 's' : ''}</span>
              </div>

              {/* Sessions */}
              <div className="divide-y divide-surface-800">
                {sessions.map((s, i) => (
                  <div key={i} className="flex items-center justify-between px-5 py-4">
                    <div className="flex items-center gap-4">
                      <div className={`px-2.5 py-1 rounded-lg text-xs font-medium capitalize ${SESSION_COLORS[s.session_type] || 'bg-slate-500/15 text-slate-400'}`}>
                        {s.session_type}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-200">{s.course_name}</p>
                        <p className="text-xs text-slate-500">{s.course_code}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock size={13} />
                        <span>{s.start_time} → {s.end_time}</span>
                      </div>
                      <span className="text-xs text-slate-600">
                        Late after {s.late_after_minutes} min
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}