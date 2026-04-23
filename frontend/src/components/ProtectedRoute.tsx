import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import type { UserRole } from '../api/types'

interface Props {
  children: React.ReactNode
  requiredRole?: UserRole
  teacherRedirect?: boolean  // if true, redirect teachers to /admin
}

export const ProtectedRoute = ({ children, requiredRole, teacherRedirect }: Props) => {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }

  // Teachers and admins always go to /admin, never to student pages
  if (teacherRedirect && (user?.role === 'teacher' || user?.role === 'admin')) {
    return <Navigate to="/admin" replace />
  }

  // Students cannot access teacher pages
  if (requiredRole && user?.role !== requiredRole && user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}
