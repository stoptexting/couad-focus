'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { sprintsApi } from '@/lib/api/sprints'
import { queryKeys } from '@/lib/queryClient'
import { Sprint, CreateSprintDto, UpdateSprintDto } from '@/lib/types'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface SprintFormModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  projectId: string
  sprint?: Sprint | null
  mode: 'create' | 'edit'
}

export function SprintFormModal({
  open,
  onOpenChange,
  projectId,
  sprint,
  mode,
}: SprintFormModalProps) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [status, setStatus] = useState<'planned' | 'active' | 'completed'>('planned')
  const [errors, setErrors] = useState<{ name?: string; dates?: string }>({})

  useEffect(() => {
    if (mode === 'edit' && sprint) {
      setName(sprint.name)
      setStartDate(sprint.start_date || '')
      setEndDate(sprint.end_date || '')
      setStatus(sprint.status)
    } else {
      setName('')
      setStartDate('')
      setEndDate('')
      setStatus('planned')
    }
    setErrors({})
  }, [mode, sprint, open])

  const createMutation = useMutation({
    mutationFn: (data: CreateSprintDto) => sprintsApi.createSprint(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.sprints(projectId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) })
      onOpenChange(false)
    },
    onError: (error: Error) => {
      setErrors({ name: error.message })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: UpdateSprintDto) => sprintsApi.updateSprint(sprint!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.sprints(projectId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.sprint(sprint!.id) })
      onOpenChange(false)
    },
    onError: (error: Error) => {
      setErrors({ name: error.message })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    // Validation
    if (!name.trim()) {
      setErrors({ name: 'Sprint name is required' })
      return
    }

    if (name.length > 100) {
      setErrors({ name: 'Sprint name must be 100 characters or less' })
      return
    }

    // Validate date range
    if (startDate && endDate && new Date(endDate) < new Date(startDate)) {
      setErrors({ dates: 'End date must be after start date' })
      return
    }

    const data = {
      name: name.trim(),
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      status,
    }

    if (mode === 'create') {
      createMutation.mutate(data)
    } else {
      updateMutation.mutate(data)
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? 'Create New Sprint' : 'Edit Sprint'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? 'Create a new sprint to organize your user stories.'
              : 'Update your sprint details.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">
              Sprint Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Sprint 1"
              maxLength={100}
              disabled={isLoading}
            />
            <div className="flex justify-between">
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name}</p>
              )}
              <p className="text-xs text-muted-foreground ml-auto">
                {name.length}/100
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="startDate">Start Date</Label>
              <Input
                id="startDate"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="endDate">End Date</Label>
              <Input
                id="endDate"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={isLoading}
              />
            </div>
          </div>
          {errors.dates && (
            <p className="text-sm text-destructive">{errors.dates}</p>
          )}

          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select value={status} onValueChange={(value: any) => setStatus(value)} disabled={isLoading}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="planned">Planned</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : mode === 'create' ? 'Create Sprint' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
