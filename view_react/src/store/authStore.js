// view-react/src/store/authStore.js
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAuthStore = create(
  persist(
    (set, get) => ({
      accessToken:  null,
      refreshToken: null,
      userName:     null,
      role:         null,   // "admin" | "student"
      studentId:    null,   // only set when role = "student"
      orgId:        1,

      login: (data) => set({
        accessToken:  data.access_token,
        refreshToken: data.refresh_token,
        userName:     data.user_name,
        role:         data.role,
        studentId:    data.student_id || null,
      }),

      logout: () => set({
        accessToken:  null,
        refreshToken: null,
        userName:     null,
        role:         null,
        studentId:    null,
      }),

      setTokens: (access, refresh) => set({
        accessToken:  access,
        refreshToken: refresh,
      }),

      setOrgId: (id) => set({ orgId: id }),

      isLoggedIn: () => !!get().accessToken,
      isAdmin:    () => get().role === 'admin',
      isStudent:  () => get().role === 'student',
    }),
    { name: 'auth-store' }
  )
)

export default useAuthStore