'use client'

import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  RefreshCw,
  LogOut,
  FolderKanban,
  ChevronRight,
  Check,
  Circle,
  Loader2,
  AlertCircle,
  ExternalLink,
} from 'lucide-react'
import { taigaApi } from '@/lib/api/taiga'
import { queryKeys } from '@/lib/queryClient'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollReveal } from '@/components/animations/ScrollReveal'
import { useTaigaVersion } from '@/hooks/useTaigaVersion'
import type { Sprint, UserStory, Task } from '@/lib/types'

const TAIGA_HOST = 'taiga.imt-atlantique.fr'

export default function TaigaPage() {
  const queryClient = useQueryClient()

  // Get current config
  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: queryKeys.taigaConfig,
    queryFn: taigaApi.getConfig,
    refetchInterval: 30000, // Check every 30 seconds
    refetchIntervalInBackground: true,
  })

  // Initialize LED display on first page load
  useEffect(() => {
    taigaApi.initLed().catch(() => {
      // Silently ignore LED init errors
    })
  }, [])

  // Render based on state
  if (configLoading) {
    return <LoadingState />
  }

  if (!config?.authenticated) {
    return <LoginForm />
  }

  if (!config?.has_project) {
    return <ProjectForm username={config.username || ''} />
  }

  return <ProjectTreeView config={config} />
}

// ============================================================================
// Loading State
// ============================================================================

function LoadingState() {
  return (
    <div className="container mx-auto p-8">
      <div className="space-y-4">
        <div className="h-12 bg-neo-lightgrey border-neo border-neo-black w-64 animate-pulse" />
        <div className="h-96 bg-neo-lightgrey border-neo border-neo-black animate-pulse" />
      </div>
    </div>
  )
}

// ============================================================================
// Login Form
// ============================================================================

function LoginForm() {
  const queryClient = useQueryClient()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const loginMutation = useMutation({
    mutationFn: (credentials?: { username: string; password: string }) => {
      const user = credentials?.username || username
      const pass = credentials?.password || password
      return taigaApi.login(user, pass)
    },
    onSuccess: () => {
      setError('')
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaConfig })
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaMyProjects })
    },
    onError: (err: Error) => {
      setError(err.message || 'Login failed. Please check your credentials.')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password) {
      setError('Please enter both username and password')
      return
    }
    loginMutation.mutate({ username, password })
  }

  return (
    <div className="container mx-auto p-8 max-w-md">
      <ScrollReveal animation="fade-in-up">
        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-neo-blue border-neo border-neo-black shadow-neo flex items-center justify-center mb-4 -rotate-3">
              <FolderKanban className="h-8 w-8 text-white" />
            </div>
            <CardTitle className="text-2xl">Connect to Taiga</CardTitle>
            <CardDescription>
              Enter your Taiga credentials to sync project data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username" className="font-display uppercase text-xs tracking-wide">
                  Username
                </Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="your.username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={loginMutation.isPending}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="font-display uppercase text-xs tracking-wide">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="********"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loginMutation.isPending}
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 text-sm text-neo-error bg-neo-error/10 p-3 border-neo-sm border-neo-error">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </div>
              )}

              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    loginMutation.mutate({ username: 'api_focus', password: 'reswoj-0xeBxu-zarqor' })
                  }}
                  disabled={loginMutation.isPending}
                >
                  {loginMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Connecting...
                    </>
                  ) : (
                    'Use API Account'
                  )}
                </Button>
                <Button
                  type="submit"
                  className="flex-1"
                  disabled={loginMutation.isPending}
                >
                  {loginMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Connecting...
                    </>
                  ) : (
                    'Login'
                  )}
                </Button>
              </div>

              <p className="text-xs text-center text-neo-grey font-mono mt-4">
                Server: {TAIGA_HOST}
              </p>
            </form>
          </CardContent>
        </Card>
      </ScrollReveal>
    </div>
  )
}

// ============================================================================
// Project Form
// ============================================================================

function ProjectForm({ username }: { username: string }) {
  const queryClient = useQueryClient()
  const [projectUrl, setProjectUrl] = useState('')
  const [error, setError] = useState('')

  // Fetch user's projects
  const { data: myProjects, isLoading: projectsLoading } = useQuery({
    queryKey: queryKeys.taigaMyProjects,
    queryFn: taigaApi.getMyProjects,
  })

  // Fetch pending memberships
  const { data: pendingMemberships } = useQuery({
    queryKey: queryKeys.taigaPendingMemberships,
    queryFn: taigaApi.getPendingMemberships,
  })

  const setProjectMutation = useMutation({
    mutationFn: (url: string) => taigaApi.setProject(url),
    onSuccess: () => {
      setError('')
      // Trigger initial sync after setting project
      syncMutation.mutate()
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to connect to project')
    },
  })

  const syncMutation = useMutation({
    mutationFn: taigaApi.sync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaConfig })
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaTree })
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to sync project data')
    },
  })

  const logoutMutation = useMutation({
    mutationFn: taigaApi.logout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaConfig })
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaMyProjects })
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaPendingMemberships })
    },
  })

  const acceptInvitationMutation = useMutation({
    mutationFn: taigaApi.acceptInvitation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaMyProjects })
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaPendingMemberships })
    },
  })

  const handleProjectSelect = (url: string) => {
    setError('')
    setProjectMutation.mutate(url)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectUrl.trim()) {
      setError('Please enter a project URL')
      return
    }
    if (!projectUrl.includes('/project/')) {
      setError('Invalid URL format. Use: https://taiga.imt-atlantique.fr/project/your-project/')
      return
    }
    setProjectMutation.mutate(projectUrl)
  }

  const isPending = setProjectMutation.isPending || syncMutation.isPending

  const pendingCount = (pendingMemberships?.invitations?.length || 0) + (pendingMemberships?.requests?.length || 0)

  return (
    <div className="container mx-auto p-8 max-w-lg">
      <ScrollReveal animation="fade-in-up">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Welcome, {username}!</CardTitle>
                <CardDescription>Select or connect to a Taiga project</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => logoutMutation.mutate()}
                disabled={logoutMutation.isPending}
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Your Projects Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="font-display uppercase text-sm tracking-wide">Your Projects</Label>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => queryClient.invalidateQueries({ queryKey: queryKeys.taigaMyProjects })}
                  disabled={projectsLoading}
                >
                  <RefreshCw className={`h-4 w-4 ${projectsLoading ? 'animate-spin' : ''}`} />
                </Button>
              </div>
              {projectsLoading ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-neo-grey" />
                </div>
              ) : myProjects?.projects && myProjects.projects.length > 0 ? (
                <div className="space-y-2">
                  {myProjects.projects.map((project) => (
                    <button
                      key={project.id}
                      onClick={() => handleProjectSelect(project.url)}
                      disabled={isPending}
                      className="w-full flex items-center justify-between p-4 border-neo-sm border-neo-black bg-white shadow-neo-sm hover:shadow-neo hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all text-left disabled:opacity-50"
                    >
                      <div>
                        <div className="font-display font-bold text-sm uppercase">{project.name}</div>
                        {project.description && (
                          <div className="text-xs text-neo-grey font-body truncate max-w-[300px]">
                            {project.description}
                          </div>
                        )}
                      </div>
                      <ChevronRight className="h-4 w-4 text-neo-grey" />
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-neo-grey font-body py-2">
                  You are not a member of any projects yet
                </p>
              )}
            </div>

            {/* Separator */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t-neo-sm border-neo-black" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-white px-4 font-display uppercase text-xs tracking-wide text-neo-grey">
                  Or join a new project
                </span>
              </div>
            </div>

            {/* Manual URL Entry */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="projectUrl" className="font-display uppercase text-xs tracking-wide">
                  Project URL
                </Label>
                <Input
                  id="projectUrl"
                  type="url"
                  placeholder={`https://${TAIGA_HOST}/project/your-project/`}
                  value={projectUrl}
                  onChange={(e) => setProjectUrl(e.target.value)}
                  disabled={isPending}
                />
                <p className="text-xs text-neo-grey font-mono">
                  Copy the URL from your Taiga project page
                </p>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-sm text-neo-error bg-neo-error/10 p-3 border-neo-sm border-neo-error">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {syncMutation.isPending ? 'Syncing...' : 'Connecting...'}
                  </>
                ) : (
                  'Connect to Project'
                )}
              </Button>
            </form>

            {/* Pending Invitations */}
            {pendingCount > 0 && (
              <>
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t-neo-sm border-neo-black" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-white px-4 font-display uppercase text-xs tracking-wide text-neo-grey">
                      Pending Invitations ({pendingCount})
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  {pendingMemberships?.invitations?.map((inv) => (
                    <div
                      key={inv.id}
                      className="flex items-center justify-between p-4 border-neo-sm border-neo-black bg-neo-blue-light"
                    >
                      <div>
                        <div className="font-display font-bold text-sm">{inv.project_name}</div>
                        <div className="text-xs text-neo-grey font-mono">
                          Role: {inv.role_name}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => acceptInvitationMutation.mutate(inv.id)}
                        disabled={acceptInvitationMutation.isPending}
                      >
                        {acceptInvitationMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          'Accept'
                        )}
                      </Button>
                    </div>
                  ))}
                  {pendingMemberships?.requests?.map((req) => (
                    <div
                      key={req.id}
                      className="flex items-center justify-between p-4 border-neo-sm border-neo-black bg-neo-lightgrey"
                    >
                      <div>
                        <div className="font-display font-bold text-sm">{req.project_name}</div>
                        <div className="text-xs text-neo-grey font-mono">
                          Status: {req.status}
                        </div>
                      </div>
                      <span className="text-xs text-neo-grey font-mono">
                        Waiting for approval
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </ScrollReveal>
    </div>
  )
}

// ============================================================================
// Project Tree View
// ============================================================================

interface ConfigWithProject {
  username: string | null
  project_url: string | null
  project_slug: string | null
  last_sync_at: string | null
  sync_status: string
}

function ProjectTreeView({ config }: { config: ConfigWithProject }) {
  const queryClient = useQueryClient()

  // Auto-refresh interval state (persisted to localStorage)
  const [refreshInterval, setRefreshInterval] = useState<number>(120000)
  const hasLoadedRef = useRef(false)

  // Combined load/save effect to avoid race condition
  useEffect(() => {
    if (!hasLoadedRef.current) {
      // First run: load from localStorage
      const saved = localStorage.getItem('taiga-refresh-interval')
      if (saved) {
        const parsed = parseInt(saved, 10)
        if (parsed !== refreshInterval) {
          setRefreshInterval(parsed)
          return // Don't save yet, let the state update trigger another run
        }
      }
      hasLoadedRef.current = true
    } else {
      // Subsequent runs: save to localStorage
      localStorage.setItem('taiga-refresh-interval', refreshInterval.toString())
    }
  }, [refreshInterval])

  // Enable smart polling for real-time updates via webhooks
  // When a webhook is received, data_version increments and this triggers cache invalidation
  useTaigaVersion(true)

  // Get project tree
  const { data: tree, isLoading: treeLoading, dataUpdatedAt } = useQuery({
    queryKey: queryKeys.taigaTree,
    queryFn: taigaApi.getTree,
    refetchInterval: refreshInterval,
    refetchIntervalInBackground: true,
  })

  // Mutations
  const syncMutation = useMutation({
    mutationFn: taigaApi.sync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaConfig })
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaTree })
    },
  })

  // Auto-sync effect - actually sync from Taiga at the configured interval
  useEffect(() => {
    if (refreshInterval <= 0) return

    const intervalId = setInterval(() => {
      // Only sync if not already syncing
      if (!syncMutation.isPending) {
        syncMutation.mutate()
      }
    }, refreshInterval)

    return () => clearInterval(intervalId)
  }, [refreshInterval, syncMutation])

  const disconnectMutation = useMutation({
    mutationFn: taigaApi.disconnectProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaConfig })
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaTree })
    },
  })

  const logoutMutation = useMutation({
    mutationFn: taigaApi.logout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaConfig })
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaTree })
    },
  })

  // Format last sync time
  const formatLastSync = (isoString: string | null) => {
    if (!isoString) return 'Never'
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min ago`
    return date.toLocaleTimeString()
  }

  if (treeLoading) {
    return <LoadingState />
  }

  return (
    <div className="container mx-auto p-8">
      {/* Header */}
      <ScrollReveal animation="fade-in-down">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="font-display font-bold text-3xl md:text-4xl uppercase tracking-tight flex items-center gap-3">
              <div className="w-12 h-12 bg-neo-blue border-neo border-neo-black shadow-neo flex items-center justify-center -rotate-3">
                <FolderKanban className="h-6 w-6 text-white" />
              </div>
              {tree?.project?.name || 'Project'}
            </h1>
            <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-neo-grey font-mono">
              <span className="px-2 py-1 bg-neo-lightgrey border-neo-sm border-neo-black">
                Last sync: {formatLastSync(dataUpdatedAt ? new Date(dataUpdatedAt).toISOString() : config.last_sync_at)}
              </span>
              <Select
                value={refreshInterval.toString()}
                onValueChange={(value) => setRefreshInterval(parseInt(value, 10))}
              >
                <SelectTrigger className="w-auto h-auto px-2 py-1 bg-neo-blue-light border-neo-sm border-neo-black text-neo-blue text-sm font-mono gap-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5000">Auto-refresh: 5 sec</SelectItem>
                  <SelectItem value="120000">Auto-refresh: 2 min</SelectItem>
                  <SelectItem value="300000">Auto-refresh: 5 min</SelectItem>
                </SelectContent>
              </Select>
              {config.project_url && (
                <a
                  href={config.project_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 px-2 py-1 bg-white border-neo-sm border-neo-black hover:bg-neo-blue-light transition-colors"
                >
                  View in Taiga <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
            >
              {syncMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => disconnectMutation.mutate()}
              disabled={disconnectMutation.isPending}
            >
              Change Project
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => logoutMutation.mutate()}
              disabled={logoutMutation.isPending}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </ScrollReveal>

      {/* Project Progress */}
      {tree?.project && (
        <ScrollReveal animation="fade-in-up" delay={100}>
          <div className="mb-6 p-4 bg-white border-neo border-neo-black shadow-neo">
            <div className="flex items-center justify-between mb-3">
              <span className="font-display font-bold uppercase text-sm">Overall Progress</span>
              <span className="font-mono text-neo-blue text-lg font-bold">
                {tree.project.progress?.percentage ?? 0}%
              </span>
            </div>
            <div className="neo-progress">
              <div
                className="neo-progress-bar"
                style={{ width: `${tree.project.progress?.percentage ?? 0}%` }}
              />
            </div>
          </div>
        </ScrollReveal>
      )}

      {/* Sprint Tree */}
      <ScrollReveal animation="fade-in-up" delay={200}>
        {tree?.sprints && tree.sprints.length > 0 ? (
          <div className="bg-white border-neo border-neo-black shadow-neo p-4">
            <Accordion type="multiple" className="w-full">
              {tree.sprints.map((sprint, index) => (
                <SprintItem key={sprint.id} sprint={sprint} index={index} />
              ))}
            </Accordion>
          </div>
        ) : (
          <div className="border-neo border-dashed border-neo-grey bg-neo-offwhite">
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-20 h-20 bg-neo-lightgrey border-neo border-neo-black flex items-center justify-center mb-4">
                <FolderKanban className="h-10 w-10 text-neo-grey" />
              </div>
              <h3 className="font-display font-bold text-xl uppercase mb-2">No sprints found</h3>
              <p className="text-neo-grey font-body">
                Create sprints in Taiga to see them here
              </p>
            </div>
          </div>
        )}
      </ScrollReveal>
    </div>
  )
}

// ============================================================================
// Tree Components
// ============================================================================

interface ProgressInfo {
  percentage: number
  total_sprints?: number
  completed_sprints?: number
  total_stories?: number
  completed_stories?: number
  total_tasks?: number
  completed_tasks?: number
}

interface SprintWithProgress extends Sprint {
  progress: ProgressInfo
  user_stories: UserStoryWithProgress[]
}

interface UserStoryWithProgress extends UserStory {
  progress: ProgressInfo
  tasks: Task[]
}

function SprintItem({ sprint, index }: { sprint: SprintWithProgress; index: number }) {
  const statusStyles =
    sprint.status === 'completed'
      ? 'bg-neo-success text-white'
      : sprint.status === 'active'
        ? 'bg-neo-blue text-white'
        : 'bg-neo-lightgrey text-neo-black'

  return (
    <AccordionItem value={sprint.id}>
      <AccordionTrigger>
        <div className="flex items-center gap-3 flex-1 pr-4">
          <div className="flex-1 text-left">
            <div className="flex items-center gap-2 flex-wrap">
              <span>{sprint.name}</span>
              <span className={`px-2 py-0.5 text-[10px] font-mono uppercase ${statusStyles}`}>
                {sprint.status}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-24 h-3 bg-neo-lightgrey border border-neo-black overflow-hidden hidden sm:block">
              <div
                className="h-full bg-neo-blue transition-all"
                style={{ width: `${sprint.progress?.percentage ?? 0}%` }}
              />
            </div>
            <span className="font-mono text-sm text-neo-blue w-12 text-right">
              {sprint.progress?.percentage ?? 0}%
            </span>
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent>
        {sprint.user_stories && sprint.user_stories.length > 0 ? (
          <div className="space-y-2 pt-2">
            {sprint.user_stories.map((story) => (
              <UserStoryItem key={story.id} story={story} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-neo-grey py-2 font-body">No user stories</p>
        )}
      </AccordionContent>
    </AccordionItem>
  )
}

function UserStoryItem({ story }: { story: UserStoryWithProgress }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="border-neo-sm border-neo-black overflow-hidden bg-neo-offwhite">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 p-3 hover:bg-neo-blue-light transition-colors"
      >
        <ChevronRight
          className={`h-4 w-4 shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}
        />
        <div className="flex-1 text-left">
          <span className="text-sm font-body">
            {story.taiga_ref ? (
              <span className="font-mono text-neo-blue">#{story.taiga_ref}</span>
            ) : null}
            {' '}{story.title}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-16 h-2 bg-neo-lightgrey border border-neo-black overflow-hidden hidden sm:block">
            <div
              className="h-full bg-neo-success transition-all"
              style={{ width: `${story.progress?.percentage ?? 0}%` }}
            />
          </div>
          <span className="font-mono text-xs text-neo-grey w-10 text-right">
            {story.progress?.percentage ?? 0}%
          </span>
        </div>
      </button>

      {isOpen && story.tasks && story.tasks.length > 0 && (
        <div className="border-t border-neo-lightgrey bg-white px-3 py-2">
          <div className="space-y-1">
            {story.tasks.map((task) => (
              <TaskItem key={task.id} task={task} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function TaskItem({ task }: { task: Task }) {
  const isCompleted = task.status === 'completed'

  return (
    <div className={`flex items-center gap-2 py-2 px-3 text-sm ${isCompleted ? 'bg-neo-success/10' : ''}`}>
      {isCompleted ? (
        <div className="w-5 h-5 bg-neo-success border border-neo-black flex items-center justify-center">
          <Check className="h-3 w-3 text-white" />
        </div>
      ) : (
        <div className="w-5 h-5 border-neo-sm border-neo-black bg-white" />
      )}
      <span className={`font-body ${isCompleted ? 'text-neo-grey line-through' : ''}`}>
        {task.taiga_ref ? (
          <span className="font-mono text-neo-blue">#{task.taiga_ref}</span>
        ) : null}
        {' '}{task.title}
      </span>
    </div>
  )
}
