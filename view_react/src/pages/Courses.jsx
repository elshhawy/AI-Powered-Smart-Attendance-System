// view-react/src/pages/Courses.jsx
import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BookOpen, Plus, ChevronDown, ChevronRight, Clock, Trash2,
  Pencil, X, Loader2, ToggleLeft, ToggleRight, Calendar
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  listCourses, createCourse, updateCourse, deleteCourse,
  addCourseSession, updateCourseSession, deleteCourseSession,
  getActiveSession, listOrganizations
} from '../api'
import useAuthStore from '../store/authStore'
import clsx from 'clsx'

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const SESSION_TYPE_COLORS = {
  lecture:  'bg-blue-500/15 text-blue-400 border-blue-500/20',
  section:  'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  lab:      'bg-purple-500/15 text-purple-400 border-purple-500/20',
  tutorial: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  exam:     'bg-red-500/15 text-red-400 border-red-500/20',
}

const SessionTypeBadge = ({ type }) => {
  const color = SESSION_TYPE_COLORS[type] || 'bg-slate-500/15 text-slate-400 border-slate-500/20'
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${color}`}>
      {type}
    </span>
  )
}

export default function Courses() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState({})
  const [activeSession, setActiveSession] = useState(null)
  const [showCourseModal, setShowCourseModal] = useState(false)
  const [showSessionModal, setShowSessionModal] = useState(null) // course_id
  const [editingCourse, setEditingCourse] = useState(null)
  const [editingSession, setEditingSession] = useState(null)
  const [orgMap, setOrgMap] = useState({}) // <-- NEW STATE
  const { orgId, role } = useAuthStore()

  const load = async () => {
    setLoading(true)
    try {
      const [coursesRes, activeRes] = await Promise.all([
        listCourses(orgId),
        getActiveSession(orgId),
      ])
      setCourses(coursesRes.data.courses || [])
      setActiveSession(activeRes.data)
// <-- NEW: Fetch and map organization names for Super Admin -->
      if (role === 'super_admin') {
        const orgsRes = await listOrganizations()
        const map = {}
        orgsRes.data.forEach(o => { map[o.id] = o.name })
        setOrgMap(map)
      }
    } catch { toast.error('Failed to load courses') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [orgId])

  const toggleExpand = (id) => setExpanded(prev => ({ ...prev, [id]: !prev[id] }))

  const handleToggleCourse = async (course) => {
    try {
      await updateCourse(course.id, { is_active: !course.is_active })
      toast.success(`Course ${course.is_active ? 'deactivated' : 'activated'}`)
      load()
    } catch { toast.error('Failed to update course') }
  }

  const handleDeleteCourse = async (course) => {
    if (!confirm(`Delete "${course.name}" and all its sessions?`)) return
    try {
      await deleteCourse(course.id)
      toast.success('Course deleted')
      load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Delete failed') }
  }

  const handleDeleteSession = async (sessionId) => {
    if (!confirm('Delete this session?')) return
    try {
      await deleteCourseSession(sessionId)
      toast.success('Session deleted')
      load()
    } catch { toast.error('Delete failed') }
  }

  const handleToggleSession = async (session) => {
    try {
      await updateCourseSession(session.id, { is_active: !session.is_active })
      load()
    } catch { toast.error('Failed to update session') }
  }

  const groupedCourses = courses.reduce((groups, course) => {
    const org = course.organization_id || 'Unassigned'
    if (!groups[org]) groups[org] = []
    groups[org].push(course)
    return groups
  }, {})

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Courses</h1>
          <p className="page-subtitle mt-1">{courses.length} courses — manage schedules dynamically</p>
        </div>
        {role !== 'super_admin' && (
          <button onClick={() => setShowCourseModal(true)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus size={15} /> Add Course
          </button>
        )}
      </div>

      {/* Active Session Banner */}
      {activeSession && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-4 border-emerald-500/20 bg-emerald-500/5 flex items-center gap-3"
        >
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          <div>
            <p className="text-sm font-medium text-emerald-300">
              Active now: <span className="text-emerald-400">{activeSession.session_type}</span>
            </p>
            <p className="text-xs text-slate-500">
              {activeSession.start_time} → {activeSession.end_time} · Late after {activeSession.late_after_minutes} min
            </p>
          </div>
        </motion.div>
      )}

      {/* Courses List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-16 bg-surface-800 rounded-2xl animate-pulse" />)}
        </div>
      ) : courses.length === 0 ? (
        <div className="card py-20 text-center">
          <BookOpen size={48} className="text-slate-700 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">No courses yet</p>
          <p className="text-sm text-slate-600 mt-1">Click "Add Course" to get started</p>
        </div>
      ) : role === 'super_admin' ? (
        <div className="space-y-8">
          {Object.entries(groupedCourses).map(([orgId, orgCourses]) => (
            <div key={orgId} className="space-y-3">
              <div className="flex items-center gap-3 pb-1 border-b border-surface-800">
                <div className="w-8 h-8 rounded-lg bg-surface-800 flex items-center justify-center text-slate-400 font-bold">#{orgId}</div>
                <h3 className="text-lg font-semibold text-slate-200">{orgMap[orgId] || `Organization ${orgId}`}</h3>
              </div>
              {orgCourses.map((course) => (
                <div key={course.id} className="card overflow-hidden">
                  <div className="flex items-center justify-between px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-surface-800 text-slate-500 flex items-center justify-center text-sm font-bold">
                        {course.code.slice(0, 2)}
                      </div>
                      <div>
                        <p className="font-semibold text-sm text-slate-400">{course.name}</p>
                        <p className="text-xs text-slate-500">{course.code} · {course.sessions.length} sessions</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {courses.map((course, i) => (
              <motion.div
                key={course.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="card overflow-hidden"
              >
                {/* Course Header */}
                <div
                  className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-surface-800/30 transition-colors"
                  onClick={() => toggleExpand(course.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className={clsx(
                      'w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold',
                      course.is_active ? 'bg-primary-600/20 text-primary-400' : 'bg-surface-800 text-slate-500'
                    )}>
                      {course.code.slice(0, 2)}
                    </div>
                    <div>
                      <p className={clsx('font-semibold text-sm', course.is_active ? 'text-slate-200' : 'text-slate-500')}>
                        {course.name}
                      </p>
                      <p className="text-xs text-slate-500">{course.code} · {course.sessions.length} sessions</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={(e) => { e.stopPropagation(); setShowSessionModal(course.id) }}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-primary-400 hover:bg-primary-500/10 transition-all" title="Add session">
                      <Plus size={14} />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); setEditingCourse(course) }}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-surface-700 transition-all">
                      <Pencil size={14} />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); handleToggleCourse(course) }}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-surface-700 transition-all">
                      {course.is_active ? <ToggleRight size={16} className="text-emerald-400" /> : <ToggleLeft size={16} />}
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); handleDeleteCourse(course) }}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all">
                      <Trash2 size={14} />
                    </button>
                    {expanded[course.id] ? <ChevronDown size={16} className="text-slate-500" /> : <ChevronRight size={16} className="text-slate-500" />}
                  </div>
                </div>

                {/* Sessions */}
                <AnimatePresence>
                  {expanded[course.id] && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="border-t border-surface-800 overflow-hidden"
                    >
                      {course.sessions.length === 0 ? (
                        <div className="px-5 py-6 text-center">
                          <p className="text-sm text-slate-500">No sessions yet</p>
                          <button onClick={() => setShowSessionModal(course.id)}
                            className="text-xs text-primary-400 hover:underline mt-1">Add first session</button>
                        </div>
                      ) : (
                        <div className="divide-y divide-surface-800">
                          {course.sessions.map(session => (
                            <div key={session.id}
                              className={clsx('flex items-center justify-between px-5 py-3',
                                !session.is_active && 'opacity-50'
                              )}>
                              <div className="flex items-center gap-3">
                                <SessionTypeBadge type={session.session_type} />
                                <div className="flex items-center gap-1.5 text-sm text-slate-400">
                                  <Calendar size={13} />
                                  <span>{DAY_NAMES[session.day_of_week]}</span>
                                </div>
                                <div className="flex items-center gap-1.5 text-sm text-slate-400">
                                  <Clock size={13} />
                                  <span>{session.start_time} → {session.end_time}</span>
                                </div>
                                <span className="text-xs text-slate-600">
                                  Late after {session.late_after_minutes} min
                                </span>
                              </div>
                              <div className="flex items-center gap-1">
                                <button onClick={() => setEditingSession(session)}
                                  className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-surface-700 transition-all">
                                  <Pencil size={13} />
                                </button>
                                <button onClick={() => handleToggleSession(session)}
                                  className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-surface-700 transition-all">
                                  {session.is_active ? <ToggleRight size={15} className="text-emerald-400" /> : <ToggleLeft size={15} />}
                                </button>
                                <button onClick={() => handleDeleteSession(session.id)}
                                  className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all">
                                  <Trash2 size={13} />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Modals */}
      <AnimatePresence>
        {showCourseModal && (
          <CourseModal orgId={orgId} onClose={() => setShowCourseModal(false)} onSuccess={() => { setShowCourseModal(false); load() }} />
        )}
        {editingCourse && (
          <CourseModal orgId={orgId} course={editingCourse} onClose={() => setEditingCourse(null)} onSuccess={() => { setEditingCourse(null); load() }} />
        )}
        {showSessionModal && (
          <SessionModal courseId={showSessionModal} onClose={() => setShowSessionModal(null)} onSuccess={() => { setShowSessionModal(null); load() }} />
        )}
        {editingSession && (
          <SessionModal session={editingSession} courseId={editingSession.course_id} onClose={() => setEditingSession(null)} onSuccess={() => { setEditingSession(null); load() }} />
        )}
      </AnimatePresence>
    </div>
  )
}

// ── Course Modal ──────────────────────────────────────────────
function CourseModal({ orgId, course, onClose, onSuccess }) {
  const [name, setName] = useState(course?.name || '')
  const [code, setCode] = useState(course?.code || '')
  const [description, setDescription] = useState(course?.description || '')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name || !code) return toast.error('Name and code are required')
    setLoading(true)
    try {
      if (course) {
        await updateCourse(course.id, { name, code, description })
        toast.success('Course updated')
      } else {
        await createCourse({ name, code, description, organization_id: orgId })
        toast.success('Course created!')
      }
      onSuccess()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed')
    } finally { setLoading(false) }
  }

  return (
    <ModalWrapper onClose={onClose} title={course ? 'Edit Course' : 'New Course'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">Course Name</label>
          <input className="input" placeholder="Artificial Intelligence" value={name} onChange={e => setName(e.target.value)} />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">Course Code</label>
          <input className="input" placeholder="CS401" value={code} onChange={e => setCode(e.target.value)} />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">Description (optional)</label>
          <input className="input" placeholder="Brief description..." value={description} onChange={e => setDescription(e.target.value)} />
        </div>
        <div className="flex gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
            {loading ? <Loader2 size={15} className="animate-spin" /> : course ? 'Update' : 'Create'}
          </button>
        </div>
      </form>
    </ModalWrapper>
  )
}

// ── Session Modal ─────────────────────────────────────────────
function SessionModal({ courseId, session, onClose, onSuccess }) {
  const [sessionType, setSessionType] = useState(session?.session_type || 'lecture')
  const [customType, setCustomType] = useState('')
  const [dayOfWeek, setDayOfWeek] = useState(session?.day_of_week ?? 6)
  const [startTime, setStartTime] = useState(session?.start_time?.slice(0, 5) || '10:00')
  const [endTime, setEndTime] = useState(session?.end_time?.slice(0, 5) || '11:00')
  const [lateAfter, setLateAfter] = useState(session?.late_after_minutes ?? 15)
  const [loading, setLoading] = useState(false)

  const PRESET_TYPES = ['lecture', 'section', 'lab', 'tutorial', 'exam', 'custom']
  const finalType = sessionType === 'custom' ? customType : sessionType

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!finalType) return toast.error('Session type is required')
    if (startTime >= endTime) return toast.error('End time must be after start time')
    setLoading(true)
    try {
      const payload = {
        session_type: finalType,
        day_of_week: Number(dayOfWeek),
        start_time: startTime + ':00',
        end_time: endTime + ':00',
        late_after_minutes: Number(lateAfter),
      }
      if (session) {
        await updateCourseSession(session.id, payload)
        toast.success('Session updated')
      } else {
        await addCourseSession(courseId, payload)
        toast.success('Session added!')
      }
      onSuccess()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed')
    } finally { setLoading(false) }
  }

  return (
    <ModalWrapper onClose={onClose} title={session ? 'Edit Session' : 'Add Session'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">Session Type</label>
          <div className="flex flex-wrap gap-2 mb-2">
            {PRESET_TYPES.map(t => (
              <button key={t} type="button"
                onClick={() => setSessionType(t)}
                className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-all border',
                  sessionType === t ? 'bg-primary-600 text-white border-primary-600' : 'bg-surface-800 text-slate-400 border-surface-700 hover:text-slate-200'
                )}
              >{t}</button>
            ))}
          </div>
          {sessionType === 'custom' && (
            <input className="input text-sm" placeholder="Enter custom type..." value={customType} onChange={e => setCustomType(e.target.value)} />
          )}
        </div>
        <div>
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">Day of Week</label>
          <select className="input" value={dayOfWeek} onChange={e => setDayOfWeek(e.target.value)}>
            {DAY_NAMES.map((d, i) => <option key={i} value={i}>{d}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Start Time</label>
            <input type="time" className="input" value={startTime} onChange={e => setStartTime(e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">End Time</label>
            <input type="time" className="input" value={endTime} onChange={e => setEndTime(e.target.value)} />
          </div>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">
            Late after (minutes) — currently {lateAfter} min after start
          </label>
          <input type="number" min={0} max={120} className="input" value={lateAfter} onChange={e => setLateAfter(e.target.value)} />
        </div>
        <div className="flex gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
            {loading ? <Loader2 size={15} className="animate-spin" /> : session ? 'Update' : 'Add Session'}
          </button>
        </div>
      </form>
    </ModalWrapper>
  )
}

// ── Modal Wrapper ─────────────────────────────────────────────
function ModalWrapper({ onClose, title, children }) {
  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
        className="card w-full max-w-md p-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-surface-800 transition-all">
            <X size={16} />
          </button>
        </div>
        {children}
      </motion.div>
    </motion.div>
  )
}