'use client'

import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Task, CreateTaskDto, UpdateTaskDto } from '@/lib/types'
import { tasksApi } from '@/lib/api/tasks'
import { queryKeys } from '@/lib/queryClient'

interface TaskFormModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  userStoryId: string
  task?: Task | null
  mode: 'create' | 'edit'
}

export function TaskFormModal({
  open,
  onOpenChange,
  userStoryId,
  task,
  mode,
}: TaskFormModalProps) {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState<{ title?: string; description?: string }>({})

  // Populate form when editing
  useEffect(() => {
    if (mode === 'edit' && task) {
      setTitle(task.title)
      setDescription(task.description || '')
    } else {
      setTitle('')
      setDescription('')
    }
    setErrors({})
  }, [mode, task, open])

  const createMutation = useMutation({
    mutationFn: (data: CreateTaskDto) => tasksApi.createTask(userStoryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks(userStoryId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.userStory(userStoryId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.userStoryProgress(userStoryId) })
      // Also invalidate parent queries
      queryClient.invalidateQueries({ queryKey: ['sprints'] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      onOpenChange(false)
      resetForm()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: UpdateTaskDto }) =>
      tasksApi.updateTask(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks(userStoryId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.task(task!.id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.userStory(userStoryId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.userStoryProgress(userStoryId) })
      // Also invalidate parent queries
      queryClient.invalidateQueries({ queryKey: ['sprints'] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      onOpenChange(false)
      resetForm()
    },
  })

  const resetForm = () => {
    setTitle('')
    setDescription('')
    setErrors({})
  }

  const validate = () => {
    const newErrors: { title?: string; description?: string } = {}

    if (!title.trim()) {
      newErrors.title = 'Title is required'
    } else if (title.length > 100) {
      newErrors.title = 'Title must be 100 characters or less'
    }

    if (description.length > 500) {
      newErrors.description = 'Description must be 500 characters or less'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    const taskData = {
      title: title.trim(),
      description: description.trim() || undefined,
    }

    if (mode === 'create') {
      createMutation.mutate(taskData)
    } else if (mode === 'edit' && task) {
      updateMutation.mutate({
        id: task.id,
        updates: taskData,
      })
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? 'Create New Task' : 'Edit Task'}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="title">
                Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter task title"
                maxLength={100}
                disabled={isPending}
              />
              <div className="flex justify-between">
                {errors.title && (
                  <p className="text-sm text-destructive">{errors.title}</p>
                )}
                <p className="text-xs text-muted-foreground ml-auto">
                  {title.length}/100
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter task description (optional)"
                maxLength={500}
                rows={4}
                disabled={isPending}
              />
              {errors.description && (
                <p className="text-sm text-destructive">{errors.description}</p>
              )}
              <p className="text-xs text-muted-foreground text-right">
                {description.length}/500
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending
                ? 'Saving...'
                : mode === 'create'
                ? 'Create Task'
                : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
