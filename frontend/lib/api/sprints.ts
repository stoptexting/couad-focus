import apiClient from './client'
import { Sprint, CreateSprintDto, UpdateSprintDto, SprintProgress, UserStory } from '../types'

export const sprintsApi = {
  getSprintsByProject: async (projectId: string): Promise<Sprint[]> => {
    const { data } = await apiClient.get(`/projects/${projectId}/sprints`)
    return data
  },

  getSprint: async (id: string): Promise<Sprint> => {
    const { data } = await apiClient.get(`/sprints/${id}`)
    return data
  },

  createSprint: async (projectId: string, sprint: CreateSprintDto): Promise<Sprint> => {
    const { data } = await apiClient.post(`/projects/${projectId}/sprints`, sprint)
    return data
  },

  updateSprint: async (id: string, updates: UpdateSprintDto): Promise<Sprint> => {
    const { data } = await apiClient.put(`/sprints/${id}`, updates)
    return data
  },

  deleteSprint: async (id: string): Promise<void> => {
    await apiClient.delete(`/sprints/${id}`)
  },

  getSprintProgress: async (id: string): Promise<SprintProgress> => {
    const { data} = await apiClient.get(`/sprints/${id}/progress`)
    return data
  },

  getUserStories: async (sprintId: string): Promise<UserStory[]> => {
    const { data } = await apiClient.get(`/sprints/${sprintId}/user-stories`)
    return data
  },
}
