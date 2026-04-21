import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { login, getMe } from '../api/auth'

export const LoginPage = () => {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const tokenData = await login({ username, password })
      localStorage.setItem('token', tokenData.access_token)
      const user = await getMe()
      setAuth(tokenData.access_token, user)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">🚩</div>
          <h1 className="text-2xl font-bold text-white">CTF Platform</h1>
          <p className="text-gray-400 text-sm mt-1">ASIR · Seguridad y Alta Disponibilidad</p>
        </div>

        {/* Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                placeholder="your.username"
                autoComplete="username"
                required
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </div>

            {error && (
              <div className="bg-red-950 border border-red-800 rounded-lg px-3 py-2 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        </div>

        <p className="text-center text-gray-600 text-xs mt-6">
          Use the credentials provided by your teacher
        </p>
      </div>
    </div>
  )
}
