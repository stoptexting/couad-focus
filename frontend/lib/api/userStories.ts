import apiClient from './client'
import { UserStory, CreateUserStoryDto, UpdateUserStoryDto, UserStoryProgress } from '../types'

export const userStoriesApi = {
  getUserStoriesBySprint: async (sprintId: string): Promise<UserStory[]> => {
    const { data } = await apiClient.get(`/sprints/${sprintId}/user-stories`)
    return data
  },

  getUserStory: async (id: string): Promise<UserStory> => {
    const { data } = await apiClient.get(`/user-stories/${id}`)
    return data
  },

  createUserStory: async (sprintId: string, userStory: CreateUserStoryDto): Promise<UserStory> => {
    const { data } = await apiClient.post(`/sprints/${sprintId}/user-stories`, userStory)
    return data
  },

  updateUserStory: async (id: string, updates: UpdateUserStoryDto): Promise<UserStory> => {
    const { data } = await apiClient.put(`/user-stories/${id}`, updates)
    return data
  },

  deleteUserStory: async (id: string): Promise<void> => {
    await apiClient.delete(`/user-stories/${id}`)
  },

  getUserStoryProgress: async (id: string): Promise<UserStoryProgress> => {
    const { data } = await apiClient.get(`/user-stories/${id}/progress`)
    return data
  },
}
