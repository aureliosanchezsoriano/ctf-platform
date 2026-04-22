import client from './client'

export interface StudentProgress {
  id: string
  username: string
  full_name: string
  class_name: string | null
  points: number
  solved_count: number
  total_challenges: number
  is_active: boolean
}

export interface ContainerEntry {
  name: string
  status: string
  user: string
  challenge: string
  short_id: string
}

export interface ImportResult {
  created: number
  skipped: number
  errors: string[]
}

export const getStudents = async (): Promise<StudentProgress[]> => {
  const res = await client.get<StudentProgress[]>('/admin/students')
  return res.data
}

export const toggleStudent = async (userId: string): Promise<{ id: string; is_active: boolean }> => {
  const res = await client.patch(`/admin/students/${userId}/toggle`)
  return res.data
}

export const killStudentContainers = async (userId: string): Promise<{ stopped: number }> => {
  const res = await client.delete(`/admin/students/${userId}/containers`)
  return res.data
}

export const getContainers = async (): Promise<ContainerEntry[]> => {
  const res = await client.get<ContainerEntry[]>('/admin/containers')
  return res.data
}

export const killAllContainers = async (): Promise<{ stopped: number }> => {
  const res = await client.delete('/admin/containers/all')
  return res.data
}

export const importStudents = async (file: File, className?: string): Promise<ImportResult> => {
  const form = new FormData()
  form.append('file', file)
  if (className) form.append('class_name', className)
  const res = await client.post<ImportResult>('/admin/import/students', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export const exportResults = () => {
  const token = localStorage.getItem('token')
  const url = '/api/admin/export/results'
  const a = document.createElement('a')
  a.href = url
  a.download = 'ctf_results.xlsx'
  // Add auth header via fetch then trigger download
  fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    .then(r => r.blob())
    .then(blob => {
      const blobUrl = URL.createObjectURL(blob)
      a.href = blobUrl
      a.click()
      URL.revokeObjectURL(blobUrl)
    })
}
