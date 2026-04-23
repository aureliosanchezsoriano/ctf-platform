import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import {
  getStudents, getContainers, toggleStudent,
  killAllContainers, importStudents, exportResults,
  getAdminChallenges, resetStudentProgress,
  deleteStudent, createStudent,
  type CreateStudentRequest,
} from '../../api/admin'
import { activateChallenge, deactivateChallenge } from '../../api/challenges'

interface ChallengeRowProps {
  challenge: { slug: string; name: string; category: string; points: number; is_active: boolean }
  onActivate: (slug: string) => void
  onDeactivate: (slug: string) => void
}

const ChallengeRow = ({ challenge, onActivate, onDeactivate }: ChallengeRowProps) => {
  const [pending, setPending] = useState(false)

  const handleToggle = async () => {
    setPending(true)
    try {
      if (challenge.is_active) {
        await onDeactivate(challenge.slug)
      } else {
        await onActivate(challenge.slug)
      }
    } finally {
      setPending(false)
    }
  }

  return (
    <tr className="border-b border-gray-800 last:border-0">
      <td className="px-4 py-3">
        <div className="font-medium text-white">{challenge.name}</div>
        <div className="text-gray-500 text-xs">{challenge.slug}</div>
      </td>
      <td className="px-4 py-3 text-gray-400">{challenge.category}</td>
      <td className="px-4 py-3 text-center">
        <span className={`text-xs px-2 py-0.5 rounded-full border ${
          challenge.is_active
            ? 'bg-green-950 text-green-400 border-green-900'
            : 'bg-gray-800 text-gray-500 border-gray-700'
        }`}>
          {challenge.is_active ? 'active' : 'inactive'}
        </span>
      </td>
      <td className="px-4 py-3 text-right text-white">{challenge.points}</td>
      <td className="px-4 py-3 text-right">
        <button
          onClick={handleToggle}
          disabled={pending}
          className={`text-xs transition-colors disabled:opacity-50 ${
            challenge.is_active
              ? 'text-red-500 hover:text-red-400'
              : 'text-green-500 hover:text-green-400'
          }`}
        >
          {pending ? '...' : challenge.is_active ? 'Deactivate' : 'Activate'}
        </button>
      </td>
    </tr>
  )
}

interface ChallengesTabProps {
  challenges: { slug: string; name: string; category: string; points: number; is_active: boolean }[]
  onActivate: (slug: string) => void
  onDeactivate: (slug: string) => void
}

const ChallengesTab = ({ challenges, onActivate, onDeactivate }: ChallengesTabProps) => (
  <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-800">
          <th className="text-left text-gray-500 font-medium px-4 py-3">Challenge</th>
          <th className="text-left text-gray-500 font-medium px-4 py-3">Category</th>
          <th className="text-center text-gray-500 font-medium px-4 py-3">Status</th>
          <th className="text-right text-gray-500 font-medium px-4 py-3">Points</th>
          <th className="text-right text-gray-500 font-medium px-4 py-3">Actions</th>
        </tr>
      </thead>
      <tbody>
        {challenges.map(challenge => (
          <ChallengeRow
            key={challenge.slug}
            challenge={challenge}
            onActivate={onActivate}
            onDeactivate={onDeactivate}
          />
        ))}
      </tbody>
    </table>
  </div>
)

export const AdminDashboard = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user, clearAuth } = useAuthStore()
  const [activeTab, setActiveTab] = useState<'students' | 'challenges' | 'containers' | 'import'>('students')
  const [importClass, setImportClass] = useState('')
  const [importResult, setImportResult] = useState<{ created: number; skipped: number; errors: string[] } | null>(null)
  const [showAddStudent, setShowAddStudent] = useState(false)
  const [newStudent, setNewStudent] = useState<CreateStudentRequest>({
    username: '', full_name: '', email: '', password: '', class_name: ''
  })
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: students } = useQuery({ queryKey: ['admin-students'], queryFn: getStudents, refetchInterval: 15_000 })
  const { data: containers } = useQuery({ queryKey: ['admin-containers'], queryFn: getContainers, refetchInterval: 10_000 })
  const { data: challenges } = useQuery({ queryKey: ['challenges-admin'], queryFn: getAdminChallenges })

  const toggleMutation = useMutation({
    mutationFn: toggleStudent,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-students'] }),
  })

  const killAllMutation = useMutation({
    mutationFn: killAllContainers,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-containers'] }),
  })

  const activateMutation = useMutation({
    mutationFn: (slug: string) => activateChallenge(slug),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['challenges-admin'] }),
  })

  const deactivateMutation = useMutation({
    mutationFn: (slug: string) => deactivateChallenge(slug),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['challenges-admin'] }),
  })

  const resetProgressMutation = useMutation({
    mutationFn: resetStudentProgress,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-students'] }),
  })

  const deleteStudentMutation = useMutation({
    mutationFn: deleteStudent,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-students'] }),
  })

  const createStudentMutation = useMutation({
    mutationFn: createStudent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-students'] })
      setShowAddStudent(false)
      setNewStudent({ username: '', full_name: '', email: '', password: '', class_name: '' })
    },
  })

  const importMutation = useMutation({
    mutationFn: ({ file, className }: { file: File; className: string }) =>
      importStudents(file, className || undefined),
    onSuccess: (data) => {
      setImportResult(data)
      queryClient.invalidateQueries({ queryKey: ['admin-students'] })
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) importMutation.mutate({ file, className: importClass })
  }

  const handleLogout = () => { clearAuth(); navigate('/login') }

  const tabs = [
    { id: 'students', label: 'Students' },
    { id: 'challenges', label: 'Challenges' },
    { id: 'containers', label: 'Containers' },
    { id: 'import', label: 'Import / Export' },
  ] as const

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="border-b border-gray-800 px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🚩</span>
            <span className="font-semibold">CTF Platform</span>
            <span className="text-gray-600 text-sm">Teacher Panel</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-500 text-sm">{user?.username}</span>
            <button onClick={handleLogout} className="text-gray-500 hover:text-red-400 text-sm transition-colors">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-6">

        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-white">{students?.length ?? 0}</div>
            <div className="text-gray-500 text-xs mt-1">students</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-white">{challenges?.length ?? 0}</div>
            <div className="text-gray-500 text-xs mt-1">challenges</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-white">{containers?.filter(c => c.status === 'running').length ?? 0}</div>
            <div className="text-gray-500 text-xs mt-1">containers running</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-white">
              {students ? Math.round((students.filter(s => s.solved_count > 0).length / Math.max(students.length, 1)) * 100) : 0}%
            </div>
            <div className="text-gray-500 text-xs mt-1">participation</div>
          </div>
        </div>

        <div className="flex gap-1 mb-6 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'students' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">{students?.length ?? 0} students</span>
              <button
                onClick={() => setShowAddStudent(!showAddStudent)}
                className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
              >
                {showAddStudent ? 'Cancel' : 'Add student'}
              </button>
            </div>

            {showAddStudent && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <h3 className="font-medium text-white mb-4">New student</h3>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder="Username"
                    value={newStudent.username}
                    onChange={e => setNewStudent(s => ({ ...s, username: e.target.value }))}
                    className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                  <input
                    type="text"
                    placeholder="Full name"
                    value={newStudent.full_name}
                    onChange={e => setNewStudent(s => ({ ...s, full_name: e.target.value }))}
                    className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                  <input
                    type="email"
                    placeholder="Email"
                    value={newStudent.email}
                    onChange={e => setNewStudent(s => ({ ...s, email: e.target.value }))}
                    className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                  <input
                    type="password"
                    placeholder="Password"
                    value={newStudent.password}
                    onChange={e => setNewStudent(s => ({ ...s, password: e.target.value }))}
                    className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                  <input
                    type="text"
                    placeholder="Class name (optional)"
                    value={newStudent.class_name ?? ''}
                    onChange={e => setNewStudent(s => ({ ...s, class_name: e.target.value }))}
                    className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={() => createStudentMutation.mutate(newStudent)}
                    disabled={createStudentMutation.isPending || !newStudent.username || !newStudent.email || !newStudent.password || !newStudent.full_name}
                    className="bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
                  >
                    {createStudentMutation.isPending ? 'Creating...' : 'Create student'}
                  </button>
                </div>
                {createStudentMutation.isError && (
                  <p className="text-red-400 text-xs mt-2">
                    {(createStudentMutation.error as any)?.response?.data?.detail ?? 'Error creating student'}
                  </p>
                )}
              </div>
            )}

            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left text-gray-500 font-medium px-4 py-3">Student</th>
                    <th className="text-left text-gray-500 font-medium px-4 py-3">Class</th>
                    <th className="text-center text-gray-500 font-medium px-4 py-3">Progress</th>
                    <th className="text-right text-gray-500 font-medium px-4 py-3">Points</th>
                    <th className="text-right text-gray-500 font-medium px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {students?.map(student => (
                    <tr key={student.id} className="border-b border-gray-800 last:border-0">
                      <td className="px-4 py-3">
                        <div className="font-medium text-white">{student.full_name}</div>
                        <div className="text-gray-500 text-xs">{student.username}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-400">{student.class_name ?? '-'}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 justify-center">
                          <div className="w-24 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-indigo-500 rounded-full"
                              style={{ width: `${(student.solved_count / Math.max(student.total_challenges, 1)) * 100}%` }}
                            />
                          </div>
                          <span className="text-gray-400 text-xs">{student.solved_count}/{student.total_challenges}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-white">{student.points}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex gap-3 justify-end">
                          <button
                            onClick={() => {
                              if (window.confirm(`Reset all progress for ${student.full_name}?`)) {
                                resetProgressMutation.mutate(student.id)
                              }
                            }}
                            className="text-xs text-yellow-600 hover:text-yellow-400 transition-colors"
                          >
                            Reset
                          </button>
                          <button
                            onClick={() => toggleMutation.mutate(student.id)}
                            className={`text-xs transition-colors ${student.is_active ? 'text-orange-500 hover:text-orange-400' : 'text-green-500 hover:text-green-400'}`}
                          >
                            {student.is_active ? 'Disable' : 'Enable'}
                          </button>
                          <button
                            onClick={() => {
                              if (window.confirm(`Permanently delete ${student.full_name}? This cannot be undone.`)) {
                                deleteStudentMutation.mutate(student.id)
                              }
                            }}
                            className="text-xs text-red-500 hover:text-red-400 transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'challenges' && (
          <ChallengesTab
            challenges={challenges ?? []}
            onActivate={(slug) => activateMutation.mutate(slug)}
            onDeactivate={(slug) => deactivateMutation.mutate(slug)}
          />
        )}

        {activeTab === 'containers' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">{containers?.length ?? 0} containers</span>
              <button
                onClick={() => killAllMutation.mutate()}
                disabled={killAllMutation.isPending}
                className="bg-red-900 hover:bg-red-800 disabled:opacity-50 text-red-300 rounded-lg px-4 py-2 text-sm font-medium transition-colors border border-red-800"
              >
                {killAllMutation.isPending ? 'Stopping...' : 'Emergency stop all'}
              </button>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              {!containers?.length ? (
                <div className="text-gray-500 text-sm text-center py-8">No containers running</div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left text-gray-500 font-medium px-4 py-3">Container</th>
                      <th className="text-left text-gray-500 font-medium px-4 py-3">Challenge</th>
                      <th className="text-center text-gray-500 font-medium px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {containers?.map(c => (
                      <tr key={c.short_id} className="border-b border-gray-800 last:border-0">
                        <td className="px-4 py-3 font-mono text-xs text-gray-400">{c.name}</td>
                        <td className="px-4 py-3 text-white">{c.challenge}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${
                            c.status === 'running'
                              ? 'bg-green-950 text-green-400 border-green-900'
                              : 'bg-gray-800 text-gray-500 border-gray-700'
                          }`}>
                            {c.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {activeTab === 'import' && (
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h3 className="font-medium text-white mb-1">Import students from Excel</h3>
              <p className="text-gray-500 text-xs mb-4">
                Required columns: username, full_name, email, password, class_name (optional)
              </p>
              <div className="space-y-3">
                <input
                  type="text"
                  value={importClass}
                  onChange={e => setImportClass(e.target.value)}
                  placeholder="Default class name (optional)"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500"
                />
                <input ref={fileInputRef} type="file" accept=".xlsx,.xls" onChange={handleFileChange} className="hidden" />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={importMutation.isPending}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
                >
                  {importMutation.isPending ? 'Importing...' : 'Upload Excel file'}
                </button>
                {importResult && (
                  <div className="bg-gray-800 rounded-lg p-3 text-xs space-y-1">
                    <div className="text-green-400">Created: {importResult.created}</div>
                    <div className="text-yellow-400">Skipped: {importResult.skipped}</div>
                    {importResult.errors.map((e, i) => (
                      <div key={i} className="text-red-400">{e}</div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h3 className="font-medium text-white mb-1">Export results</h3>
              <p className="text-gray-500 text-xs mb-4">
                Download an Excel file with all student scores for your gradebook.
              </p>
              <button
                onClick={exportResults}
                className="w-full bg-green-700 hover:bg-green-600 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
              >
                Download results.xlsx
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
