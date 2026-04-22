import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { getChallenges } from '../api/challenges'
import { getScoreboard } from '../api/scoreboard'
import type { Challenge } from '../api/types'

const difficultyColor = {
  easy: 'bg-green-950 text-green-400 border-green-900',
  medium: 'bg-yellow-950 text-yellow-400 border-yellow-900',
  hard: 'bg-red-950 text-red-400 border-red-900',
}

const categoryColor: Record<string, string> = {
  web: 'bg-blue-950 text-blue-400 border-blue-900',
  crypto: 'bg-purple-950 text-purple-400 border-purple-900',
  forensics: 'bg-teal-950 text-teal-400 border-teal-900',
  pwn: 'bg-orange-950 text-orange-400 border-orange-900',
  misc: 'bg-gray-800 text-gray-400 border-gray-700',
}

const ChallengeCard = ({ challenge }: { challenge: Challenge }) => {
  const navigate = useNavigate()

  const handleClick = () => {
    if (!challenge.locked) navigate(`/challenges/${challenge.slug}`)
  }

  return (
    <div
      onClick={handleClick}
      className={`
        bg-gray-900 border rounded-xl p-4 transition-all
        ${challenge.solved
          ? 'border-l-2 border-l-green-500 border-gray-800'
          : challenge.locked
            ? 'border-gray-800 opacity-50 cursor-not-allowed'
            : 'border-gray-800 hover:border-gray-600 cursor-pointer hover:bg-gray-800'
        }
      `}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${categoryColor[challenge.category] ?? categoryColor.misc}`}>
              {challenge.category}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${difficultyColor[challenge.difficulty]}`}>
              {challenge.difficulty}
            </span>
            {challenge.owasp_ref && (
              <span className="text-xs px-2 py-0.5 rounded-full border bg-gray-800 text-gray-400 border-gray-700">
                {challenge.owasp_ref}
              </span>
            )}
            {challenge.solved && (
              <span className="text-xs px-2 py-0.5 rounded-full border bg-green-950 text-green-400 border-green-900">
                ✓ solved
              </span>
            )}
            {challenge.locked && (
              <span className="text-xs px-2 py-0.5 rounded-full border bg-gray-800 text-gray-500 border-gray-700">
                🔒 locked
              </span>
            )}
          </div>
          <h3 className="text-white font-medium text-sm leading-snug">
            {challenge.name}
          </h3>
          <p className="text-gray-500 text-xs mt-1 line-clamp-2">
            {challenge.description}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-white font-semibold text-lg">{challenge.points}</div>
          <div className="text-gray-500 text-xs">pts</div>
        </div>
      </div>
    </div>
  )
}

export const DashboardPage = () => {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const { data: challenges, isLoading: loadingChallenges } = useQuery({
    queryKey: ['challenges'],
    queryFn: getChallenges,
  })

  const { data: scoreboard } = useQuery({
    queryKey: ['scoreboard'],
    queryFn: getScoreboard,
  })

  const myRank = scoreboard?.find(e => e.username === user?.username)
  const totalPoints = myRank?.points ?? 0
  const solvedCount = myRank?.solved_count ?? 0
  const totalChallenges = challenges?.length ?? 0

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* Navbar */}
      <nav className="border-b border-gray-800 px-6 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🚩</span>
            <span className="font-semibold text-white">CTF Platform</span>
          </div>
          <div className="flex items-center gap-4">
	  <button
	    onClick={() => navigate('/scoreboard')}
	    className="text-gray-400 hover:text-white text-sm transition-colors"
	  >
	    Scoreboard
	  </button>
	  {(user?.role === 'teacher' || user?.role === 'admin') && (
	    <button
	      onClick={() => navigate('/admin')}
	      className="text-indigo-400 hover:text-indigo-300 text-sm transition-colors"
	    >
	      Admin
	    </button>
	  )}
            <span className="text-gray-600 text-sm">{user?.username}</span>
            <button
              onClick={handleLogout}
              className="text-gray-500 hover:text-red-400 text-sm transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8">

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-white">{totalPoints}</div>
            <div className="text-gray-500 text-sm mt-1">points</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-white">
              {solvedCount}<span className="text-gray-600 text-lg">/{totalChallenges}</span>
            </div>
            <div className="text-gray-500 text-sm mt-1">solved</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-white">
              {myRank ? `#${myRank.rank}` : '—'}
            </div>
            <div className="text-gray-500 text-sm mt-1">rank</div>
          </div>
        </div>

        {/* Challenge list */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-white font-semibold">Challenges</h2>
          <span className="text-gray-500 text-sm">{totalChallenges} available</span>
        </div>

        {loadingChallenges ? (
          <div className="text-gray-500 text-sm text-center py-12">Loading challenges...</div>
        ) : challenges?.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-12">
            No challenges available yet. Check back later.
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {challenges?.map(c => <ChallengeCard key={c.slug} challenge={c} />)}
          </div>
        )}
      </div>
    </div>
  )
}
