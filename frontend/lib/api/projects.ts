import apiClient from './client'
import { Project, CreateProjectDto, UpdateProjectDto, ProjectProgress } from '../types'

export const projectsApi = {
  getProjects: async (): Promise<Project[]> => {
    const { data } = await apiClient.get('/projects')
    return data
  },

  getProject: async (id: string): Promise<Project> => {
    const { data } = await apiClient.get(`/projects/${id}`)
    return data
  },

  createProject: async (project: CreateProjectDto): Promise<Project> => {
    const { data } = await apiClient.post('/projects', project)
    return data
  },

  updateProject: async (id: string, updates: UpdateProjectDto): Promise<Project> => {
    const { data} = await apiClient.put(`/projects/${id}`, updates)
    return data
  },

  deleteProject: async (id: string): Promise<void> => {
    await apiClient.delete(`/projects/${id}`)
  },

  getProjectProgress: async (id: string): Promise<ProjectProgress> => {
    const { data } = await apiClient.get(`/projects/${id}/progress`)
    return data
  },

  updatePreferredLayout: async (id: string, layout: string): Promise<Project> => {
    const { data } = await apiClient.put(`/projects/${id}/preferred-layout`, { preferred_layout: layout })
    return data
  },

  updatePreferredSprintIndex: async (id: string, sprintIndex: number): Promise<Project> => {
    const { data } = await apiClient.put(`/projects/${id}/preferred-sprint-index`, { preferred_sprint_index: sprintIndex })
    return data
  },
}
