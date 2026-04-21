import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getChallenge, submitFlag } from '../api/challenges'
import { getHintStatus, revealHint } from '../api/hints'

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

export const ChallengePage = () => {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [flag, setFlag] = useState('')
  const [result, setResult] = useState<{ correct: boolean; message: string } | null>(null)

  const { data: challenge, isLoading } = useQuery({
    queryKey: ['challenge', slug],
    queryFn: () => getChallenge(slug!),
    enabled: !!slug,
  })

  const { data: hintStatus } = useQuery({
    queryKey: ['hints', slug],
    queryFn: () => getHintStatus(slug!),
    enabled: !!slug,
  })

  const flagMutation = useMutation({
    mutationFn: (f: string) => submitFlag(slug!, f),
    onSuccess: (data) => {
      setResult({ correct: data.correct, message: data.message })
      if (data.correct) {
        queryClient.invalidateQueries({ queryKey: ['challenges'] })
        queryClient.invalidateQueries({ queryKey: ['scoreboard'] })
        queryClient.invalidateQueries({ queryKey: ['challenge', slug] })
        setFlag('')
      }
    },
    onError: (err: any) => {
      setResult({
        correct: false,
        message: err.response?.data?.detail ?? 'Submission failed',
      })
    },
  })

  const hintMutation = useMutation({
    mutationFn: (index: number) => revealHint(slug!, index),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hints', slug] })
      queryClient.invalidateQueries({ queryKey: ['scoreboard'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!flag.trim()) return
    setResult(null)
    flagMutation.mutate(flag.trim())
  }

  const isRevealed = (index: number) =>
    hintStatus?.revealed.includes(index) ?? false

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <span className="text-gray-500">Loading...</span>
      </div>
    )
  }

  if (!challenge) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <span className="text-gray-500">Challenge not found.</span>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
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

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3 flex-wrap">
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
          </div>
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-2xl font-bold text-white">{challenge.name}</h1>
            <div className="text-right flex-shrink-0">
              <div className="text-2xl font-bold text-white">{challenge.points}</div>
              <div className="text-gray-500 text-xs">points</div>
	      {!challenge.solved && hintStatus && hintStatus.points_spent > 0 && (
  		<span className="ml-2 text-yellow-600 font-normal">
    		  (−{hintStatus.points_spent} pts spent)
  		</span>
		)}
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-5">
          <h2 className="text-sm font-medium text-gray-400 mb-3">Description</h2>
          <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
            {challenge.description}
          </p>
        </div>

        {/* Hints */}
        {challenge.hints.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-5">
            <h2 className="text-sm font-medium text-gray-400 mb-3">
              Hints
              {hintStatus && hintStatus.points_spent > 0 && (
                <span className="ml-2 text-yellow-600 font-normal">
                  (−{hintStatus.points_spent} pts spent)
                </span>
              )}
            </h2>
            <div className="space-y-2">
              {challenge.hints.map((hint) => {
                const revealed = isRevealed(hint.index) || hint.cost === 0
                return (
                  <div key={hint.index} className="border border-gray-800 rounded-lg p-3">
                    {revealed ? (
                      <div className="flex items-start gap-2">
                        <span className="text-yellow-500 text-xs mt-0.5">💡</span>
                        <p className="text-gray-300 text-sm">{hint.text}</p>
                      </div>
                    ) : (
                      <button
                        onClick={() => hintMutation.mutate(hint.index)}
                        disabled={hintMutation.isPending}
                        className="w-full text-left text-gray-500 text-sm hover:text-gray-300 transition-colors disabled:opacity-50"
                      >
                        🔒 Reveal hint
                        {hint.cost > 0 && (
                          <span className="ml-2 text-xs text-yellow-600">−{hint.cost} pts</span>
                        )}
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Flag submission */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-medium text-gray-400 mb-3">Submit Flag</h2>
          {challenge.solved ? (
            <div className="bg-green-950 border border-green-900 rounded-lg px-4 py-3 text-green-400 text-sm">
              ✓ You have already solved this challenge.
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                type="text"
                value={flag}
                onChange={e => setFlag(e.target.value)}
                placeholder="CTF{...}"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                autoComplete="off"
                spellCheck={false}
              />
              {result && (
                <div className={`rounded-lg px-3 py-2 text-sm border ${
                  result.correct
                    ? 'bg-green-950 border-green-900 text-green-400'
                    : 'bg-red-950 border-red-900 text-red-400'
                }`}>
                  {result.correct ? '✓ ' : '✗ '}{result.message}
                </div>
              )}
              <button
                type="submit"
                disabled={flagMutation.isPending || !flag.trim()}
                className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
              >
                {flagMutation.isPending ? 'Checking...' : 'Submit Flag'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
