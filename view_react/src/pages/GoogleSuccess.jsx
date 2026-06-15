// view-react/src/pages/GoogleSuccess.jsx
import { useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import useAuthStore from '../store/authStore'

export default function GoogleSuccess() {
  const navigate      = useNavigate()
  const { login }     = useAuthStore()
  const [params]      = useSearchParams()
  const processed     = useRef(false)

  useEffect(() => {
    // Prevent double execution in React StrictMode
    if (processed.current) return
    processed.current = true

    const accessToken  = params.get('access_token')
    const refreshToken = params.get('refresh_token')
    const role         = params.get('role')
    const name         = params.get('name')
    const error        = params.get('error')

    // Handle error from backend
    if (error) {
      toast.error(`Google login failed: ${error}`)
      navigate('/login', { replace: true })
      return
    }

    if (!accessToken || !role) {
      toast.error('Google login failed. Please try again.')
      navigate('/login', { replace: true })
      return
    }

    // Save to store
    login({
      access_token:  accessToken,
      refresh_token: refreshToken || '',
      user_name:     name || '',
      role:          role,
      student_id:    null,
    })

    toast.success(`Welcome, ${name}! 👋`)

    // Redirect based on role
    const dest = role === 'student' ? '/student/dashboard' : '/dashboard'
    navigate(dest, { replace: true })

  }, [params])

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 size={40} className="animate-spin text-primary-400 mx-auto" />
        <p className="text-slate-400">Signing you in with Google...</p>
      </div>
    </div>
  )
}