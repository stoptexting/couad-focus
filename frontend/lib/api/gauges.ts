import apiClient from './client'
import { GaugeLayoutResponse, LayoutType, LEDSyncStatus } from '../types'

export const gaugesApi = {
  getLayoutData: async (projectId: string, layout: LayoutType, sprintIndex?: number): Promise<GaugeLayoutResponse> => {
    const params = sprintIndex !== undefined ? { sprint_index: sprintIndex } : {}
    const { data } = await apiClient.get(`/projects/${projectId}/gauges/${layout}`, { params })
    return data
  },

  syncWithLEDs: async (projectId: string): Promise<LEDSyncStatus> => {
    const { data } = await apiClient.post(`/projects/${projectId}/sync-leds`)
    return data
  },

  syncLEDMatrix: async (projectId: string, layoutType: LayoutType, sprintIndex?: number): Promise<LEDSyncStatus> => {
    const body = sprintIndex !== undefined ? { sprint_index: sprintIndex } : {}
    const { data } = await apiClient.post(`/projects/${projectId}/sync-led-matrix/${layoutType}`, body)
    return data
  },
}
