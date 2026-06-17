// view-react/src/api/index.js
import client from './client'

const KIOSK_KEY = import.meta.env.VITE_KIOSK_KEY || 'kiosk-secret-key-change-this-in-production-123'
const API_URL   = import.meta.env.VITE_API_URL   || 'http://localhost:8000'

// ── Auth ──────────────────────────────────────────────────────
export const login  = (email, password) => client.post('/api/v1/auth/login',  { email, password })
export const signup = (data)            => client.post('/api/v1/auth/signup', data)
export const getMe  = ()                => client.get('/api/v1/auth/me')
export const linkStudent = (data)       => client.post('/api/v1/auth/link-student', data)
export const listUsers   = ()           => client.get('/api/v1/auth/users')
export const googleLoginUrl = ()        => `${API_URL}/api/v1/auth/google`

// ── Students ──────────────────────────────────────────────────
export const listStudents  = (orgId) => orgId ? client.get(`/api/v1/students/organization/${orgId}`) : client.get(`/api/v1/students/`)
export const getStudent    = (id)    => client.get(`/api/v1/students/${id}`)
export const enrollStudent = (fd)    => client.post('/api/v1/students/enroll', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
export const deleteStudent = (id)    => client.delete(`/api/v1/students/${id}`)

// ── Attendance ────────────────────────────────────────────────
export const processFrame       = (fd, orgId = null) =>
  client.post(`/api/v1/attendance/process${orgId ? `?org_id=${orgId}` : ''}`, fd, {
    headers: { 'Content-Type': 'multipart/form-data', 'X-Api-Key': KIOSK_KEY, Authorization: undefined },
  })
export const getTodayAttendance = (orgId)             => orgId ? client.get(`/api/v1/attendance/today/${orgId}`) : client.get(`/api/v1/attendance/today/all`)
export const getAttendanceRange = (orgId, start, end) => orgId ? client.get(`/api/v1/attendance/range/${orgId}?start_date=${start}&end_date=${end}`) : client.get(`/api/v1/attendance/range/all?start_date=${start}&end_date=${end}`)
export const markAbsents        = (orgId)             => orgId ? client.post(`/api/v1/attendance/mark-absent/${orgId}`) : client.post(`/api/v1/attendance/mark-absent/all`)
export const getStudentStats    = (id, start, end)    => client.get(`/api/v1/attendance/statistics/${id}?start_date=${start}&end_date=${end}`)

// ── Courses ───────────────────────────────────────────────────
export const listCourses         = (orgId)            => orgId ? client.get(`/api/v1/courses/organization/${orgId}`) : client.get(`/api/v1/courses/`)
export const getCourse           = (id)               => client.get(`/api/v1/courses/${id}`)
export const createCourse        = (data)             => client.post('/api/v1/courses', data)
export const updateCourse        = (id, data)         => client.put(`/api/v1/courses/${id}`, data)
export const deleteCourse        = (id)               => client.delete(`/api/v1/courses/${id}`)
export const addCourseSession    = (courseId, data)   => client.post(`/api/v1/courses/${courseId}/sessions`, data)
export const listCourseSessions  = (courseId)         => client.get(`/api/v1/courses/${courseId}/sessions`)
export const updateCourseSession = (id, data)         => client.put(`/api/v1/courses/sessions/${id}`, data)
export const deleteCourseSession = (id)               => client.delete(`/api/v1/courses/sessions/${id}`)
export const getActiveSession    = (orgId)            => orgId ? client.get(`/api/v1/courses/active-session/${orgId}`) : client.get(`/api/v1/courses/active-session/all`)
// ── Student Portal ────────────────────────────────────────────
export const getMyProfile    = ()           => client.get('/api/v1/student/me')
export const getMyAttendance = (days = 30)  => client.get(`/api/v1/student/attendance?days=${days}`)
export const getMySchedule   = ()           => client.get('/api/v1/student/schedule')
export const getMyStatistics = (days = 30)  => client.get(`/api/v1/student/statistics?days=${days}`)

// ── Chat ──────────────────────────────────────────────────────
export const sendChat = (message, orgId, history) =>
  client.post('/api/v1/chat', { message, organization_id: orgId || null, history })

export const googleTokenLogin = (accessToken) =>
  client.post('/api/v1/auth/google/token', { access_token: accessToken })
// ── Admin Management (super_admin only) ───────────────────────
export const createAdmin = (data) => client.post('/api/v1/auth/admins', data)