import apiClient from './client'
import { Task, ProgressStats, CreateTaskDto, UpdateTaskDto } from '../types'

export const tasksApi = {
  getTasksByUserStory: async (userStoryId: string): Promise<Task[]> => {
    const { data } = await apiClient.get(`/user-stories/${userStoryId}/tasks`)
    return data
  },

  getTask: async (id: string): Promise<Task> => {
    const { data } = await apiClient.get(`/tasks/${id}`)
    return data
  },

  createTask: async (userStoryId: string, task: CreateTaskDto): Promise<Task> => {
    const { data } = await apiClient.post(`/user-stories/${userStoryId}/tasks`, task)
    return data
  },

  updateTask: async (id: string, updates: UpdateTaskDto): Promise<Task> => {
    const { data } = await apiClient.put(`/tasks/${id}`, updates)
    return data
  },

  deleteTask: async (id: string): Promise<void> => {
    await apiClient.delete(`/tasks/${id}`)
  },

  getProgress: async (): Promise<ProgressStats> => {
    const { data } = await apiClient.get('/progress')
    return data
  },
}
