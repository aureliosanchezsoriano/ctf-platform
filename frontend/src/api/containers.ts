import client from './client'

export interface ContainerInfo {
  running: boolean
  url: string | null
  container_id: string | null
  status: string
}

export const startContainer = async (slug: string): Promise<ContainerInfo> => {
  const res = await client.post<ContainerInfo>(`/challenges/${slug}/start`)
  return res.data
}

export const stopContainer = async (slug: string): Promise<ContainerInfo> => {
  const res = await client.delete<ContainerInfo>(`/challenges/${slug}/stop`)
  return res.data
}

export const getContainerStatus = async (slug: string): Promise<ContainerInfo> => {
  const res = await client.get<ContainerInfo>(`/challenges/${slug}/status`)
  return res.data
}
