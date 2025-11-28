'use client'

import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Activity, Gauge as GaugeIcon } from 'lucide-react'
import { projectsApi } from '@/lib/api/projects'
import { gaugesApi } from '@/lib/api/gauges'
import { queryKeys } from '@/lib/queryClient'
import { Project, LayoutType } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { GaugeLayout } from '@/components/gauges/GaugeLayout'

export default function GaugesPage() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const isInitialMount = useRef(true)

  const { data: projects, isLoading } = useQuery({
    queryKey: queryKeys.projects,
    queryFn: projectsApi.getProjects,
  })

  // Get the selected project's preferred layout for auto-sync
  const { data: selectedProject } = useQuery({
    queryKey: queryKeys.project(selectedProjectId || ''),
    queryFn: () => projectsApi.getProject(selectedProjectId!),
    enabled: !!selectedProjectId,
  })

  // Auto-sync mutation
  const syncMutation = useMutation({
    mutationFn: ({ projectId, layout }: { projectId: string; layout: LayoutType }) =>
      gaugesApi.syncLEDMatrix(projectId, layout),
    onSuccess: (data) => {
      console.log('Auto-sync LED successful:', data)
    },
    onError: (error) => {
      console.error('Auto-sync LED failed:', error)
    },
  })

  // Auto-select first project if available
  useEffect(() => {
    if (projects && projects.length > 0 && !selectedProjectId) {
      setSelectedProjectId(projects[0].id)
    }
  }, [projects, selectedProjectId])

  // Auto-sync LED when project selection changes (not on initial mount)
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false
      return
    }

    if (selectedProjectId && selectedProject) {
      const layout = (selectedProject.preferred_layout as LayoutType) || 'single'
      syncMutation.mutate({ projectId: selectedProjectId, layout })
    }
  }, [selectedProjectId, selectedProject?.preferred_layout])

  const handleProjectSelect = (projectId: string) => {
    setSelectedProjectId(projectId)
  }

  if (isLoading) {
    return (
      <div className="container mx-auto p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-muted rounded w-64 mb-4" />
          <div className="h-96 bg-muted rounded" />
        </div>
      </div>
    )
  }

  if (!projects || projects.length === 0) {
    return (
      <div className="container mx-auto p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold">Gauge Visualization</h1>
            <p className="text-muted-foreground mt-2">
              Visual progress tracking with LED synchronization
            </p>
          </div>
        </div>
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <GaugeIcon className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">No projects available</h3>
            <p className="text-muted-foreground mb-4">
              Create a project first to view gauge visualizations
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold flex items-center gap-3">
            <Activity className="h-10 w-10" />
            Gauge Visualization
          </h1>
          <p className="text-muted-foreground mt-2">
            Visual progress tracking with LED synchronization
          </p>
        </div>
      </div>

      <div className="mb-6">
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Select Project:</h2>
        <div className="flex flex-wrap gap-2">
          {projects.map((project) => (
            <Button
              key={project.id}
              variant={selectedProjectId === project.id ? 'default' : 'outline'}
              onClick={() => handleProjectSelect(project.id)}
              className="h-auto py-3 px-4"
            >
              <div className="flex flex-col items-start">
                <span className="font-medium">{project.name}</span>
                {project.description && (
                  <span className="text-xs opacity-80 line-clamp-1">
                    {project.description}
                  </span>
                )}
              </div>
            </Button>
          ))}
        </div>
      </div>

      {selectedProjectId && (
        <GaugeLayout
          projectId={selectedProjectId}
          defaultLayout="single"
        />
      )}
    </div>
  )
}
