// view-react/src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import useAuthStore from './store/authStore'

// Layouts
import Layout from './components/layout/Layout'
import StudentLayout from './components/layout/StudentLayout'

// Auth pages
import Login from './pages/Login'
import GoogleSuccess from './pages/GoogleSuccess'

// Admin pages
import Dashboard from './pages/Dashboard'
import Students from './pages/Students'
import Courses from './pages/Courses'
import Camera from './pages/Camera'
import Reports from './pages/Reports'
import Chatbot from './pages/Chatbot'
import Settings from './pages/Settings'

// Student pages
import StudentDashboard from './pages/student/StudentDashboard'
import StudentAttendance from './pages/student/StudentAttendance'
import StudentSchedule from './pages/student/StudentSchedule'
import StudentChatbot from './pages/student/StudentChatbot'
import StudentProfile from './pages/student/StudentProfile'


// ── Route Guards ──────────────────────────────────────────────

const PrivateRoute = ({ children }) => {
  const { accessToken } = useAuthStore()
  return accessToken ? children : <Navigate to="/login" replace />
}

const AdminRoute = ({ children }) => {
  const { accessToken, role } = useAuthStore()
  if (!accessToken) return <Navigate to="/login" replace />
  if (!['admin', 'super_admin'].includes(role)) return <Navigate to="/student/dashboard" replace />
  return children
}

const StudentRoute = ({ children }) => {
  const { accessToken, role } = useAuthStore()
  if (!accessToken) return <Navigate to="/login" replace />
  if (role !== 'student') return <Navigate to="/dashboard" replace />
  return children
}


// ── App ───────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
            borderRadius: '12px',
            fontSize: '14px',
          },
          success: { iconTheme: { primary: '#10b981', secondary: '#f1f5f9' } },
          error:   { iconTheme: { primary: '#ef4444', secondary: '#f1f5f9' } },
        }}
      />
      <Routes>
        {/* Public */}
        <Route path="/login"                element={<Login />} />
        <Route path="/auth/google/success"  element={<GoogleSuccess />} />

        {/* Admin routes */}
        <Route path="/" element={<AdminRoute><Layout /></AdminRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="students"  element={<Students />} />
          <Route path="courses"   element={<Courses />} />
          <Route path="camera"    element={<Camera />} />
          <Route path="reports"   element={<Reports />} />
          <Route path="chat"      element={<Chatbot />} />
          <Route path="settings"  element={<Settings />} />
          <Route path="settings/add-admin" element={<Settings />} />
        </Route>

        {/* Student routes */}
        <Route path="/student" element={<StudentRoute><StudentLayout /></StudentRoute>}>
          <Route index element={<Navigate to="/student/dashboard" replace />} />
          <Route path="dashboard"  element={<StudentDashboard />} />
          <Route path="attendance" element={<StudentAttendance />} />
          <Route path="schedule"   element={<StudentSchedule />} />
          <Route path="chat"       element={<StudentChatbot />} />
          <Route path="profile"    element={<StudentProfile />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}