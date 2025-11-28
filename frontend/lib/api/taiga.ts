import apiClient from './client'
import type {
  TaigaConfig,
  TaigaLoginResponse,
  TaigaProjectResponse,
  TaigaSyncResponse,
  TaigaTreeResponse,
  TaigaValidateUrlResponse,
  TaigaMyProjectsResponse,
  TaigaPendingMembershipsResponse,
  TaigaCheckProjectResponse,
} from '../types'

export const taigaApi = {
  /**
   * Get current Taiga configuration status
   */
  getConfig: async (): Promise<TaigaConfig> => {
    const { data } = await apiClient.get('/taiga/config')
    return data
  },

  /**
   * Login to Taiga with username and password
   */
  login: async (username: string, password: string): Promise<TaigaLoginResponse> => {
    const { data } = await apiClient.post('/taiga/login', { username, password })
    return data
  },

  /**
   * Logout from Taiga (clears credentials and project)
   */
  logout: async (): Promise<{ success: boolean; message: string }> => {
    const { data } = await apiClient.post('/taiga/logout')
    return data
  },

  /**
   * Set the Taiga project to sync from
   */
  setProject: async (projectUrl: string): Promise<TaigaProjectResponse> => {
    const { data } = await apiClient.post('/taiga/project', { project_url: projectUrl })
    return data
  },

  /**
   * Disconnect from current project (keeps auth)
   */
  disconnectProject: async (): Promise<{ success: boolean; message: string }> => {
    const { data } = await apiClient.delete('/taiga/project')
    return data
  },

  /**
   * Trigger sync with Taiga (force refresh)
   */
  sync: async (): Promise<TaigaSyncResponse> => {
    const { data } = await apiClient.post('/taiga/sync')
    return data
  },

  /**
   * Get the full project tree with progress
   */
  getTree: async (): Promise<TaigaTreeResponse> => {
    const { data } = await apiClient.get('/taiga/tree')
    return data
  },

  /**
   * Validate a Taiga project URL format
   */
  validateUrl: async (url: string): Promise<TaigaValidateUrlResponse> => {
    const { data } = await apiClient.post('/taiga/validate-url', { url })
    return data
  },

  /**
   * Get all projects the user is a member of
   */
  getMyProjects: async (): Promise<TaigaMyProjectsResponse> => {
    const { data } = await apiClient.get('/taiga/my-projects')
    return data
  },

  /**
   * Get pending membership invitations and requests
   */
  getPendingMemberships: async (): Promise<TaigaPendingMembershipsResponse> => {
    const { data } = await apiClient.get('/taiga/pending-memberships')
    return data
  },

  /**
   * Accept a membership invitation
   */
  acceptInvitation: async (invitationId: number): Promise<{ success: boolean; message: string }> => {
    const { data } = await apiClient.post('/taiga/accept-invitation', { invitation_id: invitationId })
    return data
  },

  /**
   * Check if user has access to a project by URL
   */
  checkProject: async (projectUrl: string): Promise<TaigaCheckProjectResponse> => {
    const { data } = await apiClient.post('/taiga/check-project', { project_url: projectUrl })
    return data
  },

  /**
   * Get current data version for smart polling
   */
  getVersion: async (): Promise<{ version: number; last_sync_at: string | null; last_webhook_at: string | null }> => {
    const { data } = await apiClient.get('/taiga/version')
    return data
  },

  /**
   * Set webhook secret for signature verification
   */
  setWebhookConfig: async (secret: string): Promise<{ success: boolean; message: string; webhook_url: string }> => {
    const { data } = await apiClient.post('/taiga/webhook-config', { secret })
    return data
  },

  /**
   * Clear webhook configuration
   */
  clearWebhookConfig: async (): Promise<{ success: boolean; message: string }> => {
    const { data } = await apiClient.delete('/taiga/webhook-config')
    return data
  },

  /**
   * Initialize LED display with current project state
   */
  initLed: async (): Promise<{ initialized: boolean; reason?: string }> => {
    const { data } = await apiClient.post('/taiga/init-led')
    return data
  },
}
