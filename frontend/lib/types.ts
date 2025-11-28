// ============================================================================
// PROJECT
// ============================================================================

export interface Project {
  id: string
  name: string
  description: string | null
  preferred_layout?: string
  preferred_sprint_index?: number
  created_at: string
  sprints?: Sprint[]
}

export interface CreateProjectDto {
  name: string
  description?: string
}

export interface UpdateProjectDto {
  name?: string
  description?: string
}

export interface ProjectProgress {
  percentage: number
  total_sprints: number
  completed_sprints: number
}

// ============================================================================
// SPRINT
// ============================================================================

export interface Sprint {
  id: string
  name: string
  project_id: string
  start_date: string | null
  end_date: string | null
  status: 'planned' | 'active' | 'completed'
  user_stories?: UserStory[]
}

export interface CreateSprintDto {
  name: string
  start_date?: string
  end_date?: string
  status?: 'planned' | 'active' | 'completed'
}

export interface UpdateSprintDto {
  name?: string
  start_date?: string
  end_date?: string
  status?: 'planned' | 'active' | 'completed'
}

export interface SprintProgress {
  percentage: number
  total_user_stories: number
  completed_user_stories: number
}

// ============================================================================
// USER STORY
// ============================================================================

export interface UserStory {
  id: string
  title: string
  description: string | null
  sprint_id: string
  priority: 'P0' | 'P1' | 'P2'
  status: 'new' | 'in_progress' | 'completed'
  taiga_id?: number | null
  taiga_ref?: number | null
  tasks?: Task[]
}

export interface CreateUserStoryDto {
  title: string
  description?: string
  priority?: 'P0' | 'P1' | 'P2'
  status?: 'new' | 'in_progress' | 'completed'
}

export interface UpdateUserStoryDto {
  title?: string
  description?: string
  priority?: 'P0' | 'P1' | 'P2'
  status?: 'new' | 'in_progress' | 'completed'
}

export interface UserStoryProgress {
  percentage: number
  total_tasks: number
  completed_tasks: number
}

// ============================================================================
// TASK
// ============================================================================

export interface Task {
  id: string
  title: string
  description: string | null
  user_story_id: string | null
  status: 'new' | 'completed'
  taiga_id?: number | null
  taiga_ref?: number | null
  created_at: string
  updated_at: string
}

export interface CreateTaskDto {
  title: string
  description?: string
}

export interface UpdateTaskDto {
  title?: string
  description?: string
  status?: 'new' | 'completed'
}

// ============================================================================
// LEGACY (Sprint 1 compatibility)
// ============================================================================

export interface ProgressStats {
  percentage: number
  total_tasks: number
  completed_tasks: number
}

// ============================================================================
// GAUGE LAYOUTS
// ============================================================================

export type LayoutType = 'single' | 'sprint_view' | 'user_story_layout'

export interface GaugeSegment {
  percentage: number
  color: string
}

export interface GaugeData {
  id: string
  label: string
  percentage: number
  color?: string
  type?: 'project' | 'sprint' | 'user_story'
  children?: GaugeData[]
  segments?: GaugeSegment[]  // Multi-color segments for sprint view
}

export interface GaugeLayoutResponse {
  layout_type: LayoutType
  gauges: GaugeData[]
  project_id: string
  project_name: string
  timestamp: string
}

export interface LEDSyncStatus {
  synced: boolean
  zones_updated: number
  last_sync: string
  errors?: string[]
}

// ============================================================================
// LED ZONES
// ============================================================================

export interface LEDZone {
  id: string
  name: string
  start_led: number
  end_led: number
  default_color: number[]
}

export interface LEDZoneUpdate {
  zone_id: string
  percentage: number
  color?: number[]
}

export interface LEDConfig {
  zones: LEDZone[]
  total_leds: number
  is_single_zone: boolean
  primary_zone: LEDZone | null
}

// ============================================================================
// TAIGA INTEGRATION
// ============================================================================

export interface WebhookHistoryEntry {
  timestamp: string
  action: string
  entity_type: string
  entity_ref: number | null
  entity_name: string | null
  payload: Record<string, unknown>
  success: boolean
}

export interface TaigaConfig {
  configured: boolean
  authenticated: boolean
  has_project: boolean
  username: string | null
  project_url: string | null
  project_slug: string | null
  taiga_project_id: number | null
  local_project_id: string | null
  sync_status: 'not_configured' | 'authenticated' | 'syncing' | 'synced' | 'error'
  last_sync_at: string | null
  last_error: string | null
  webhook_configured: boolean
  last_webhook_at: string | null
  webhook_history: WebhookHistoryEntry[]
}

export interface TaigaLoginResponse {
  success: boolean
  username: string
  full_name: string
  message: string
}

export interface TaigaProjectResponse {
  success: boolean
  project_name: string
  project_slug: string
  taiga_project_id: number
  message: string
}

export interface TaigaSyncResponse {
  success: boolean
  summary: {
    project_synced: boolean
    sprints_created: number
    sprints_updated: number
    user_stories_created: number
    user_stories_updated: number
    tasks_created: number
    tasks_updated: number
  }
  last_sync_at: string
}

export interface TaigaProgressInfo {
  percentage: number
  total_sprints?: number
  completed_sprints?: number
  total_stories?: number
  completed_stories?: number
  total_tasks?: number
  completed_tasks?: number
}

export interface TaigaTreeResponse {
  project: (Project & { progress: TaigaProgressInfo }) | null
  sprints: (Sprint & { progress: TaigaProgressInfo; user_stories: (UserStory & { progress: TaigaProgressInfo; tasks: Task[] })[] })[]
  has_data: boolean
  last_sync_at: string | null
}

export interface TaigaValidateUrlResponse {
  valid: boolean
  slug: string | null
}

export interface TaigaProjectListItem {
  id: number
  name: string
  slug: string
  is_private: boolean
  description: string
  url: string
}

export interface TaigaMyProjectsResponse {
  success: boolean
  projects: TaigaProjectListItem[]
}

export interface TaigaInvitation {
  id: number
  project_name: string
  project_slug: string
  role_name: string
  created_date: string | null
}

export interface TaigaMembershipRequest {
  id: number
  project_name: string
  project_slug: string
  status: string
  created_date: string | null
}

export interface TaigaPendingMembershipsResponse {
  success: boolean
  invitations: TaigaInvitation[]
  requests: TaigaMembershipRequest[]
}

export interface TaigaCheckProjectResponse {
  success: boolean
  has_access: boolean
  project?: {
    id: number
    name: string
    slug: string
    is_private: boolean
  }
  error?: string
  can_request?: boolean
}
