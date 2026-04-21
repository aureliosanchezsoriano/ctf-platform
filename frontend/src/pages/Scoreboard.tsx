import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { getScoreboard } from '../api/scoreboard'

export const ScoreboardPage = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()

  const { data: scoreboard, isLoading } = useQuery({
    queryKey: ['scoreboard'],
    queryFn: getScoreboard,
    refetchInterval: 30_000, // auto-refresh every 30 seconds
  })

  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* Navbar */}
      <nav className="border-b border-gray-800 px-6 py-3">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-gray-400 hover:text-white text-sm transition-colors"
          >
            ← Back
          </button>
          <span className="text-gray-700">|</span>
          <span className="text-gray-400 text-sm">🚩 CTF Platform</span>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">Scoreboard</h1>
          <span className="text-gray-500 text-xs">Refreshes every 30s</span>
        </div>

        {isLoading ? (
          <div className="text-gray-500 text-sm text-center py-12">Loading...</div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left text-gray-500 font-medium px-4 py-3 w-12">#</th>
                  <th className="text-left text-gray-500 font-medium px-4 py-3">Student</th>
                  <th className="text-left text-gray-500 font-medium px-4 py-3 hidden sm:table-cell">Class</th>
                  <th className="text-right text-gray-500 font-medium px-4 py-3">Solved</th>
                  <th className="text-right text-gray-500 font-medium px-4 py-3">Points</th>
                </tr>
              </thead>
              <tbody>
                {scoreboard?.map((entry) => {
                  const isMe = entry.username === user?.username
                  return (
                    <tr
                      key={entry.username}
                      className={`border-b border-gray-800 last:border-0 transition-colors ${
                        isMe ? 'bg-indigo-950/40' : 'hover:bg-gray-800/50'
                      }`}
                    >
                      <td className="px-4 py-3 text-gray-500 font-mono">
                        {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className={isMe ? 'text-indigo-300 font-medium' : 'text-white'}>
                            {entry.full_name}
                          </span>
                          {isMe && (
                            <span className="text-xs text-indigo-500">(you)</span>
                          )}
                        </div>
                        <div className="text-gray-500 text-xs">{entry.username}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-400 hidden sm:table-cell">
                        {entry.class_name ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-400">
                        {entry.solved_count}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-white">
                        {entry.points}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
