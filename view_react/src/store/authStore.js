// view_react/src/store/authStore.js
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAuthStore = create(
  persist(
    (set, get) => ({
      accessToken:  null,
      refreshToken: null,
      userName:     null,
      role:         null,
      studentId:    null,
      orgId:        null,   // now sourced from token, not hardcoded

      login: (data) => set({
        accessToken:  data.access_token,
        refreshToken: data.refresh_token,
        userName:     data.user_name,
        role:         data.role,
        studentId:    data.student_id  || null,
        orgId:        data.organization_id || null,
      }),

      logout: () => set({
        accessToken:  null,
        refreshToken: null,
        userName:     null,
        role:         null,
        studentId:    null,
        orgId:        null,
      }),

      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),

      // orgId is now read-only from token; no setOrgId needed
      // kept as no-op so old callers don't crash during migration
      setOrgId: (id) => {},

      isLoggedIn:    () => !!get().accessToken,
      isAdmin:       () => get().role === 'admin',
      isSuperAdmin:  () => get().role === 'super_admin',
      isStudent:     () => get().role === 'student',
      isStaff:       () => ['admin', 'super_admin'].includes(get().role),
    }),
    { name: 'auth-store' }
  )
)

export default useAuthStore