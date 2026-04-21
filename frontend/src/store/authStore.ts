import { create } from 'zustand'
import type { AuthUser, UserRole } from '../api/types'

interface AuthState {
  token: string | null
  user: AuthUser | null
  setAuth: (token: string, user: AuthUser) => void
  clearAuth: () => void
  isAuthenticated: () => boolean
  hasRole: (role: UserRole) => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem('token'),
  user: null,

  setAuth: (token, user) => {
    localStorage.setItem('token', token)
    set({ token, user })
  },

  clearAuth: () => {
    localStorage.removeItem('token')
    set({ token: null, user: null })
  },

  isAuthenticated: () => !!get().token,

  hasRole: (role) => get().user?.role === role,
}))
