import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAuthStore = create(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      adminName: null,
      orgId: 1,

      login: (data) => set({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        adminName: data.admin_name,
      }),

      logout: () => set({
        accessToken: null,
        refreshToken: null,
        adminName: null,
      }),

      setTokens: (access, refresh) => set({
        accessToken: access,
        refreshToken: refresh,
      }),

      setOrgId: (id) => set({ orgId: id }),

      isLoggedIn: () => !!get().accessToken,
    }),
    { name: 'auth-store' }
  )
)

export default useAuthStore
