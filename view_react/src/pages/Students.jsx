import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Users, Plus, Search, Trash2, Loader2, X, Upload, UserCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { listStudents, enrollStudent, deleteStudent, listOrganizations } from '../api'
import useAuthStore from '../store/authStore'

export default function Students() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [orgMap, setOrgMap] = useState({}) // <-- NEW STATE
  const { orgId, role } = useAuthStore()

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await listStudents(orgId)
      setStudents(data.students || [])
// <-- NEW: Fetch and map organization names for Super Admin -->
      if (role === 'super_admin') {
        const orgsRes = await listOrganizations()
        const map = {}
        orgsRes.data.forEach(o => { map[o.id] = o.name })
        setOrgMap(map)
      }
    } catch { toast.error('Failed to load students') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [orgId])

  const filtered = students.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.student_code.toLowerCase().includes(search.toLowerCase())
  )

  const groupedStudents = filtered.reduce((groups, student) => {
    const org = student.organization_id || 'Unassigned'
    if (!groups[org]) groups[org] = []
    groups[org].push(student)
    return groups
  }, {})

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete ${name}?`)) return
    try {
      await deleteStudent(id)
      toast.success(`${name} removed`)
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Delete failed')
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Students</h1>
          <p className="page-subtitle mt-1">{students.length} enrolled students</p>
        </div>
        {role !== 'super_admin' && (
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus size={15} /> Enroll Student
          </button>
        )}
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          className="input pl-11"
          placeholder="Search by name or code..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-3">
            {[1,2,3,4].map(i => <div key={i} className="h-12 bg-surface-800 rounded-xl animate-pulse" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center">
            <Users size={48} className="text-slate-700 mx-auto mb-3" />
            <p className="text-slate-400 font-medium">No students found</p>
            <p className="text-sm text-slate-600 mt-1">
              {search ? 'Try a different search' : 'Click "Enroll Student" to get started'}
            </p>
          </div>
        ) : role === 'super_admin' ? (
          <div className="p-6 space-y-8">
            {Object.entries(groupedStudents).map(([orgId, orgStudents]) => (
              <div key={orgId} className="space-y-4">
                <div className="flex items-center gap-3 pb-2 border-b border-surface-800">
                  <div className="w-8 h-8 rounded-lg bg-surface-800 flex items-center justify-center text-slate-400 font-bold">
                    #{orgId}
                  </div>
                  <h3 className="text-lg font-semibold text-slate-200">{orgMap[orgId] || `Organization ${orgId}`}</h3>
                  <span className="text-xs text-slate-500 ml-auto">{orgStudents.length} students</span>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-surface-800">
                      {['Student','Code','Enrolled'].map(h => (
                        <th key={h} className="text-left px-4 py-2 text-xs font-medium text-slate-500">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {orgStudents.map((s) => (
                      <tr key={s.id} className="border-b border-surface-800/50 hover:bg-surface-800/30">
                        <td className="px-4 py-2 flex items-center gap-3">
                          <div className="w-6 h-6 rounded-full bg-primary-600/20 flex items-center justify-center text-primary-400 text-xs font-semibold">
                            {s.name[0].toUpperCase()}
                          </div>
                          <span className="text-slate-200 font-medium">{s.name}</span>
                        </td>
                        <td className="px-4 py-2 text-slate-400 font-mono text-xs">{s.student_code}</td>
                        <td className="px-4 py-2 text-slate-500">{s.enrollment_date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-800">
                {['Student','Code','Enrolled','Actions'].map(h => (
                  <th key={h} className="text-left px-6 py-3 text-xs font-medium text-slate-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {filtered.map((s, i) => (
                  <motion.tr
                    key={s.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="border-b border-surface-800/50 hover:bg-surface-800/30 transition-colors"
                  >
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary-600/20 flex items-center justify-center text-primary-400 text-xs font-semibold">
                          {s.name[0].toUpperCase()}
                        </div>
                        <span className="text-slate-200 font-medium">{s.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-3 text-slate-400 font-mono text-xs">{s.student_code}</td>
                    <td className="px-6 py-3 text-slate-500">{s.enrollment_date}</td>
                    <td className="px-6 py-3">
                      <button
                        onClick={() => handleDelete(s.id, s.name)}
                        className="p-1.5 rounded-lg text-slate-600 hover:text-red-400 hover:bg-red-500/10 transition-all"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        )}
      </div>

      {/* Enroll Modal */}
      <AnimatePresence>
        {showModal && (
          <EnrollModal onClose={() => setShowModal(false)} onSuccess={() => { setShowModal(false); load() }} orgId={orgId} />
        )}
      </AnimatePresence>
    </div>
  )
}

function EnrollModal({ onClose, onSuccess, orgId }) {
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [photo, setPhoto] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)

  const handlePhoto = (e) => {
    const f = e.target.files[0]
    if (!f) return
    setPhoto(f)
    setPreview(URL.createObjectURL(f))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name || !code || !photo) return toast.error('Please fill all fields')
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('name', name)
      fd.append('student_code', code)
      fd.append('organization_id', orgId)
      fd.append('face_photo', photo)
      const { data } = await enrollStudent(fd)
      toast.success(`${data.student.name} enrolled! 🎉`)
      onSuccess()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Enrollment failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="card w-full max-w-md p-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-slate-100">Enroll New Student</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-surface-800 transition-all">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Full Name</label>
            <input className="input" placeholder="Ahmed Mohamed" value={name} onChange={e => setName(e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Student Code</label>
            <input className="input" placeholder="20210001" value={code} onChange={e => setCode(e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Face Photo</label>
            <label className="flex flex-col items-center justify-center w-full h-36 border-2 border-dashed border-surface-700 rounded-xl cursor-pointer hover:border-primary-500/50 transition-all overflow-hidden">
              {preview ? (
                <img src={preview} className="w-full h-full object-cover" />
              ) : (
                <div className="flex flex-col items-center gap-2 text-slate-500">
                  <Upload size={24} />
                  <span className="text-sm">Click to upload photo</span>
                </div>
              )}
              <input type="file" accept="image/*" className="hidden" onChange={handlePhoto} />
            </label>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {loading ? <Loader2 size={15} className="animate-spin" /> : 'Enroll'}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  )
}