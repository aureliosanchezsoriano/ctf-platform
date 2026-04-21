import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import type { UserRole } from '../api/types'

interface Props {
  children: React.ReactNode
  requiredRole?: UserRole
}

export const ProtectedRoute = ({ children, requiredRole }: Props) => {
  const { isAuthenticated, hasRole } = useAuthStore()

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}
