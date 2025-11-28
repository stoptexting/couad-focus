import apiClient from './client'

export interface ResetDatabaseResponse {
  success: boolean
  message: string
  data: {
    projects: number
    sprints: number
    user_stories: number
    tasks: number
  }
}

export const adminApi = {
  resetDatabase: async (): Promise<ResetDatabaseResponse> => {
    const { data } = await apiClient.post('/admin/reset-database')
    return data
  },
}
