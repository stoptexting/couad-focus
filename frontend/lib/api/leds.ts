import apiClient from './client'
import { LEDConfig, LEDZone, LEDZoneUpdate } from '../types'

export const ledsApi = {
  getConfig: async (): Promise<LEDConfig> => {
    const { data } = await apiClient.get('/leds/config')
    return data
  },

  getZones: async (): Promise<LEDZone[]> => {
    const { data } = await apiClient.get('/leds/zones')
    return data
  },

  updateZone: async (percentage: number): Promise<void> => {
    await apiClient.post('/leds/update', { percentage })
  },

  updateMultiZone: async (updates: LEDZoneUpdate[]): Promise<void> => {
    await apiClient.post('/leds/multi-update', { zone_updates: updates })
  },
}
