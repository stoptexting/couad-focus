'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { LayoutType } from '@/lib/types'
import { gaugesApi } from '@/lib/api/gauges'
import { projectsApi } from '@/lib/api/projects'
import { queryKeys } from '@/lib/queryClient'
import { LayoutSelector } from './LayoutSelector'
import { MultiGauge } from './MultiGauge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

interface GaugeLayoutProps {
  projectId: string
  defaultLayout?: LayoutType
  className?: string
  onSyncLEDs?: () => void
}

function GaugeLayout({ projectId, defaultLayout = 'single', className, onSyncLEDs }: GaugeLayoutProps) {
  const [layout, setLayout] = useState<LayoutType>(defaultLayout)
  const [sprintIndex, setSprintIndex] = useState<number>(0)
  const queryClient = useQueryClient()

  // Fetch the project to get its preferred layout and sprints
  const { data: project } = useQuery({
    queryKey: queryKeys.project(projectId),
    queryFn: () => projectsApi.getProject(projectId),
    enabled: !!projectId,
  })

  // Load preferred layout and sprint index when project changes
  useEffect(() => {
    if (project?.preferred_layout) {
      setLayout(project.preferred_layout as LayoutType)
    }
    if (project?.preferred_sprint_index !== undefined) {
      setSprintIndex(project.preferred_sprint_index)
    }
  }, [projectId, project?.preferred_layout, project?.preferred_sprint_index])

  // Auto-sync LED panel when layout or sprint selection changes
  useEffect(() => {
    if (project?.id) {
      syncMatrixMutation.mutate()
    }
  }, [layout, sprintIndex])

  // Periodic LED auto-sync every 10 seconds (matches gauge data refresh)
  useEffect(() => {
    if (!project?.id) return

    const intervalId = setInterval(() => {
      if (!syncMatrixMutation.isPending) {
        syncMatrixMutation.mutate()
      }
    }, 10000)

    return () => clearInterval(intervalId)
  }, [project?.id, layout, sprintIndex])

  const { data: gaugeData, isLoading, error } = useQuery({
    queryKey: queryKeys.gaugeLayout(
      projectId,
      layout,
      layout === 'user_story_layout' ? sprintIndex : undefined
    ),
    queryFn: () => gaugesApi.getLayoutData(
      projectId,
      layout,
      layout === 'user_story_layout' ? sprintIndex : undefined
    ),
    refetchInterval: 10000,
  })

  const syncMatrixMutation = useMutation({
    mutationFn: () => gaugesApi.syncLEDMatrix(
      projectId,
      layout,
      layout === 'user_story_layout' ? sprintIndex : undefined
    ),
    onSuccess: (data) => {
      console.log('LED matrix sync successful:', data)
      queryClient.invalidateQueries({
        queryKey: queryKeys.gaugeLayout(
          projectId,
          layout,
          layout === 'user_story_layout' ? sprintIndex : undefined
        ),
      })
    },
    onError: (error) => {
      console.error('LED matrix sync failed:', error)
    },
  })

  const updateLayoutMutation = useMutation({
    mutationFn: (newLayout: LayoutType) => projectsApi.updatePreferredLayout(projectId, newLayout),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) })
    },
  })

  const updateSprintIndexMutation = useMutation({
    mutationFn: (newSprintIndex: number) => projectsApi.updatePreferredSprintIndex(projectId, newSprintIndex),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) })
    },
  })

  const handleLayoutChange = (newLayout: LayoutType) => {
    setLayout(newLayout)
    // Save preferred layout to backend
    updateLayoutMutation.mutate(newLayout)
  }

  const handleSprintChange = (newSprintIndex: number) => {
    setSprintIndex(newSprintIndex)
    // Save preferred sprint index to backend
    updateSprintIndexMutation.mutate(newSprintIndex)
  }

  const handleSyncLEDs = () => {
    syncMatrixMutation.mutate()
    onSyncLEDs?.()
  }

  // Expose sync function for parent component to call
  useEffect(() => {
    // Store the sync function so parent can access it
    (window as any).__gaugeLayoutSync = handleSyncLEDs
    return () => {
      delete (window as any).__gaugeLayoutSync
    }
  }, [projectId, layout, sprintIndex])

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Gauge Visualization</CardTitle>
            <CardDescription>
              {gaugeData?.project_name} - {layout.replace('_', ' ')} view
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSyncLEDs}
            disabled={syncMatrixMutation.isPending}
          >
            {syncMatrixMutation.isPending ? 'Syncing...' : 'Sync LED Matrix'}
          </Button>
        </div>

        <LayoutSelector currentLayout={layout} onLayoutChange={handleLayoutChange} className="mt-4" />

        {/* Sprint selector (only for user_story_layout) */}
        {layout === 'user_story_layout' && project?.sprints && (
          <div className="mt-4">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
              Select Sprint to Display
            </label>
            <Select value={sprintIndex.toString()} onValueChange={(value) => handleSprintChange(parseInt(value))}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a sprint" />
              </SelectTrigger>
              <SelectContent>
                {project.sprints.map((sprint: any, index: number) => (
                  <SelectItem key={sprint.id} value={index.toString()}>
                    {sprint.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex items-center justify-center h-64 text-gray-500">
            Loading gauge data...
          </div>
        )}
        {error && (
          <div className="flex items-center justify-center h-64 text-red-500">
            Error loading gauge data: {error.message}
          </div>
        )}
        {gaugeData && !isLoading && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
              Gauge Visualization
            </h3>
            <MultiGauge gauges={gaugeData.gauges} layout={layout} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export { GaugeLayout }
export default GaugeLayout
