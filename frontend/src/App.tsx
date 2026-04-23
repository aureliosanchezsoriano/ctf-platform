import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/Login'
import { DashboardPage } from './pages/Dashboard'
import { ChallengePage } from './pages/Challenge'
import { ProfilePage } from './pages/Profile'
import { ScoreboardPage } from './pages/Scoreboard'
import { AdminDashboard } from './pages/admin/AdminDashboard'
import { useAuthStore } from './store/authStore'
import { getMe } from './api/auth'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

const RoleRedirect = () => {
  const { user } = useAuthStore()
  const dest = (user?.role === 'teacher' || user?.role === 'admin') ? '/admin' : '/dashboard'
  return <Navigate to={dest} replace />
}

function AppRoutes() {
  const { token, user, setAuth, clearAuth } = useAuthStore()

  useEffect(() => {
    if (token && !user) {
      getMe().then(u => setAuth(token, u)).catch(() => clearAuth())
    }
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={
          <ProtectedRoute teacherRedirect>
            <DashboardPage />
          </ProtectedRoute>
        } />
        <Route path="/challenges/:slug" element={
          <ProtectedRoute teacherRedirect>
            <ChallengePage />
          </ProtectedRoute>
        } />
	< Route path="/profile" element={
	  <ProtectedRoute teacherRedirect><ProfilePage /></ProtectedRoute>
	} />
        <Route path="/scoreboard" element={
          <ProtectedRoute teacherRedirect>
            <ScoreboardPage />
          </ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute requiredRole="teacher">
            <AdminDashboard />
          </ProtectedRoute>
        } />
        <Route path="*" element={<RoleRedirect />} />
      </Routes>
    </BrowserRouter>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppRoutes />
    </QueryClientProvider>
  )
}
