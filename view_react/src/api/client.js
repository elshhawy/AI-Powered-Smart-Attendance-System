// view-react/src/api/client.js
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({ baseURL: API_URL })

// Attach token to every request
client.interceptors.request.use((config) => {
  const raw = localStorage.getItem('auth-store')
  if (raw) {
    const { state } = JSON.parse(raw)
    if (state?.accessToken) {
      config.headers.Authorization = `Bearer ${state.accessToken}`
    }
  }
  return config
})

// Auto-refresh on 401
client.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const raw = localStorage.getItem('auth-store')
        const { state } = JSON.parse(raw)
        const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
          refresh_token: state.refreshToken,
        })
        // Update store
        const store = JSON.parse(localStorage.getItem('auth-store'))
        store.state.accessToken = data.access_token
        localStorage.setItem('auth-store', JSON.stringify(store))
        original.headers.Authorization = `Bearer ${data.access_token}`
        return client(original)
      } catch {
        localStorage.removeItem('auth-store')
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default client