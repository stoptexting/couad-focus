import apiClient from './client'

export interface HealthStatus {
  status: 'ok' | 'error'
  timestamp?: string
}

export const healthApi = {
  check: async (): Promise<HealthStatus> => {
    const { data } = await apiClient.get('/health')
    return {
      status: data.status === 'ok' ? 'ok' : 'error',
      timestamp: new Date().toISOString()
    }
  },
}
