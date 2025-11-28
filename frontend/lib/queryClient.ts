import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 2000, // 2 seconds
    },
  },
})

// Query keys factory
export const queryKeys = {
  // Projects
  projects: ['projects'] as const,
  project: (id: string) => ['projects', id] as const,
  projectProgress: (id: string) => ['projects', id, 'progress'] as const,

  // Sprints
  sprints: (projectId: string) => ['projects', projectId, 'sprints'] as const,
  sprint: (id: string) => ['sprints', id] as const,
  sprintProgress: (id: string) => ['sprints', id, 'progress'] as const,

  // User Stories
  userStories: (sprintId: string) => ['sprints', sprintId, 'user-stories'] as const,
  userStory: (id: string) => ['user-stories', id] as const,
  userStoryProgress: (id: string) => ['user-stories', id, 'progress'] as const,

  // Tasks
  tasks: (userStoryId: string) => ['user-stories', userStoryId, 'tasks'] as const,
  task: (id: string) => ['tasks', id] as const,

  // Gauges
  gaugeLayout: (projectId: string, layout: string, sprintIndex?: number) =>
    sprintIndex !== undefined
      ? ['projects', projectId, 'gauges', layout, sprintIndex] as const
      : ['projects', projectId, 'gauges', layout] as const,
  ledConfig: ['leds', 'config'] as const,
  ledZones: ['leds', 'zones'] as const,

  // Legacy (Sprint 1 compatibility)
  progress: ['progress'] as const,

  // Taiga
  taigaConfig: ['taiga', 'config'] as const,
  taigaTree: ['taiga', 'tree'] as const,
  taigaMyProjects: ['taiga', 'my-projects'] as const,
  taigaPendingMemberships: ['taiga', 'pending-memberships'] as const,
  taigaVersion: ['taiga', 'version'] as const,
}
