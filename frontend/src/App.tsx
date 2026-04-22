import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/Login'
import { DashboardPage } from './pages/Dashboard'
import { ChallengePage } from './pages/Challenge'
import { ScoreboardPage } from './pages/Scoreboard'
import { AdminDashboard } from './pages/admin/AdminDashboard'
import { useAuthStore } from './store/authStore'
import { getMe } from './api/auth'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

function AppRoutes() {
  const { token, user, setAuth, clearAuth } = useAuthStore()

  // On app load, if we have a token but no user, fetch the user
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
          <ProtectedRoute><DashboardPage /></ProtectedRoute>
        } />
        <Route path="/challenges/:slug" element={
          <ProtectedRoute><ChallengePage /></ProtectedRoute>
        } />
        <Route path="/scoreboard" element={
          <ProtectedRoute><ScoreboardPage /></ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute requiredRole="teacher"><AdminDashboard /></ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
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
