// view_react/src/pages/Login.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { GraduationCap, Mail, Lock, ArrowRight, Loader2, User, Hash } from 'lucide-react'
import { useGoogleLogin } from '@react-oauth/google'
import toast from 'react-hot-toast'
import { login, signup, googleTokenLogin } from '../api'
import useAuthStore from '../store/authStore'

export default function Login() {
  const [tab, setTab]                 = useState('login')
  const [email, setEmail]             = useState('')
  const [password, setPassword]       = useState('')
  const [fullName, setFullName]       = useState('')
  const [studentCode, setStudentCode] = useState('')
  const [loading, setLoading]         = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const { login: storeLogin }         = useAuthStore()
  const navigate                      = useNavigate()

  // ── Email Login ────────────────────────────────────────────
  const handleLogin = async (e) => {
    e.preventDefault()
    if (!email || !password) return toast.error('Please fill all fields')
    setLoading(true)
    try {
      const { data } = await login(email, password)
      storeLogin(data)
      toast.success(`Welcome back, ${data.user_name}! 👋`)
      navigate(data.role === 'student' ? '/student/dashboard' : '/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  // Signup is students-only; role is fixed server-side
  const handleSignup = async (e) => {
    e.preventDefault()
    if (!email || !password || !fullName || !studentCode)
      return toast.error('Please fill all fields')
    if (password.length < 6) return toast.error('Password must be at least 6 characters')
    setLoading(true)
    try {
      await signup({ email, password, full_name: fullName, role: 'student', student_code: studentCode })
      toast.success('Account created! Please sign in.')
      setTab('login')
      setPassword('')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  // ── Google Login ───────────────────────────────────────────
  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setGoogleLoading(true)
      try {
        const { data } = await googleTokenLogin(tokenResponse.access_token)
        storeLogin(data)
        toast.success(`Welcome, ${data.user_name}! 👋`)
        navigate(data.role === 'student' ? '/student/dashboard' : '/dashboard')
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Google login failed')
      } finally {
        setGoogleLoading(false)
      }
    },
    onError: () => {
      toast.error('Google login failed. Please try again.')
    },
  })

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-sm relative"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-primary-600 rounded-2xl shadow-glow mb-4">
            <GraduationCap size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">SmartAttend</h1>
          <p className="text-slate-500 text-sm mt-1">AI-Powered Attendance System</p>
        </div>

        <div className="card p-8">
          {/* Tabs */}
          <div className="flex gap-1 p-1 bg-surface-800 rounded-xl mb-6">
            {['login', 'signup'].map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                  tab === t ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}>
                {t === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          {/* Google Button */}
          <button
            onClick={() => googleLogin()}
            disabled={googleLoading}
            className="w-full flex items-center justify-center gap-3 py-2.5 px-4 rounded-xl
              bg-surface-800 border border-surface-700 text-slate-200 text-sm font-medium
              hover:bg-surface-700 transition-all mb-4 disabled:opacity-50"
          >
            {googleLoading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 48 48">
                  <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                  <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                  <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                  <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                </svg>
                Continue with Google
              </>
            )}
          </button>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-surface-700" />
            <span className="text-xs text-slate-600">or</span>
            <div className="flex-1 h-px bg-surface-700" />
          </div>

          {/* Forms */}
          <AnimatePresence mode="wait">
            {tab === 'login' ? (
              <motion.form key="login"
                initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}
                onSubmit={handleLogin} className="space-y-4"
              >
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Email</label>
                  <div className="relative">
                    <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                      placeholder="you@university.edu" className="input pl-10" />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Password</label>
                  <div className="relative">
                    <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                      placeholder="••••••••" className="input pl-10" />
                  </div>
                </div>
                <button type="submit" disabled={loading}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-3">
                  {loading ? <Loader2 size={16} className="animate-spin" /> : <>Sign In <ArrowRight size={16} /></>}
                </button>
              </motion.form>
            ) : (
              <motion.form key="signup"
                initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }}
                onSubmit={handleSignup} className="space-y-4"
              >
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Full Name</label>
                  <div className="relative">
                    <User size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input type="text" value={fullName} onChange={e => setFullName(e.target.value)}
                      placeholder="Ahmed Mohamed" className="input pl-10" />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Email</label>
                  <div className="relative">
                    <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                      placeholder="you@university.edu" className="input pl-10" />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Password</label>
                  <div className="relative">
                    <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                      placeholder="min 6 characters" className="input pl-10" />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-400 mb-1.5 block">Student Code</label>
                  <div className="relative">
                    <Hash size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input type="text" value={studentCode} onChange={e => setStudentCode(e.target.value)}
                      placeholder="e.g. CS-2024-001" className="input pl-10" />
                  </div>
                  <p className="text-xs text-slate-600 mt-1">Provided by your institution</p>
                </div>
                <button type="submit" disabled={loading}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-3">
                  {loading ? <Loader2 size={16} className="animate-spin" /> : <>Create Account <ArrowRight size={16} /></>}
                </button>
              </motion.form>
            )}
          </AnimatePresence>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">Secured with JWT Authentication</p>
      </motion.div>
    </div>
  )
}