import client from './client'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const KIOSK_KEY = import.meta.env.VITE_KIOSK_KEY || 'kiosk-secret-key-change-this-in-production-123'

// ── Auth ──────────────────────────────────────────────────────
export const login = (email, password) =>
  client.post('/api/v1/auth/login', { email, password })

export const getMe = () =>
  client.get('/api/v1/auth/me')

// ── Students ──────────────────────────────────────────────────
export const listStudents = (orgId) =>
  client.get(`/api/v1/students/organization/${orgId}`)

export const getStudent = (id) =>
  client.get(`/api/v1/students/${id}`)

export const enrollStudent = (formData) =>
  client.post('/api/v1/students/enroll', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const deleteStudent = (id) =>
  client.delete(`/api/v1/students/${id}`)

export const searchStudents = (query) =>
  client.get(`/api/v1/students/search/${query}`)

// ── Attendance ────────────────────────────────────────────────
export const processFrame = (formData) =>
  client.post('/api/v1/attendance/process', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Api-Key': KIOSK_KEY,
      Authorization: undefined,  // kiosk auth — no JWT
    },
  })

export const getTodayAttendance = (orgId) =>
  client.get(`/api/v1/attendance/today/${orgId}`)

export const getAttendanceRange = (orgId, start, end) =>
  client.get(`/api/v1/attendance/range/${orgId}?start_date=${start}&end_date=${end}`)

export const markAbsents = (orgId) =>
  client.post(`/api/v1/attendance/mark-absent/${orgId}`)

export const getStudentStats = (studentId, start, end) =>
  client.get(`/api/v1/attendance/statistics/${studentId}?start_date=${start}&end_date=${end}`)

// ── Chat ──────────────────────────────────────────────────────
export const sendChat = (message, orgId, history) =>
  client.post('/api/v1/chat', { message, organization_id: orgId, history })
