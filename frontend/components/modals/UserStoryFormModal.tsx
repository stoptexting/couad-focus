'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { userStoriesApi } from '@/lib/api/userStories'
import { queryKeys } from '@/lib/queryClient'
import { UserStory, CreateUserStoryDto, UpdateUserStoryDto } from '@/lib/types'
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
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'

interface UserStoryFormModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sprintId: string
  projectId: string
  userStory?: UserStory | null
  mode: 'create' | 'edit'
}

export function UserStoryFormModal({
  open,
  onOpenChange,
  sprintId,
  projectId,
  userStory,
  mode,
}: UserStoryFormModalProps) {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState<'P0' | 'P1' | 'P2'>('P2')
  const [status, setStatus] = useState<'new' | 'in_progress' | 'completed'>('new')
  const [errors, setErrors] = useState<{ title?: string }>({})

  useEffect(() => {
    if (mode === 'edit' && userStory) {
      setTitle(userStory.title)
      setDescription(userStory.description || '')
      setPriority(userStory.priority)
      setStatus(userStory.status)
    } else {
      setTitle('')
      setDescription('')
      setPriority('P2')
      setStatus('new')
    }
    setErrors({})
  }, [mode, userStory, open])

  const createMutation = useMutation({
    mutationFn: (data: CreateUserStoryDto) => userStoriesApi.createUserStory(sprintId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.userStories(sprintId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.sprint(sprintId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) })
      onOpenChange(false)
    },
    onError: (error: Error) => {
      setErrors({ title: error.message })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: UpdateUserStoryDto) => userStoriesApi.updateUserStory(userStory!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.userStories(sprintId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.sprint(sprintId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.project(projectId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.userStory(userStory!.id) })
      onOpenChange(false)
    },
    onError: (error: Error) => {
      setErrors({ title: error.message })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    // Validation
    if (!title.trim()) {
      setErrors({ title: 'Title is required' })
      return
    }

    if (title.length > 200) {
      setErrors({ title: 'Title must be 200 characters or less' })
      return
    }

    const data = {
      title: title.trim(),
      description: description.trim() || undefined,
      priority,
      status,
    }

    if (mode === 'create') {
      createMutation.mutate(data)
    } else {
      updateMutation.mutate(data)
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  const getPriorityColor = (p: string) => {
    switch (p) {
      case 'P0':
        return 'destructive'
      case 'P1':
        return 'default'
      case 'P2':
        return 'secondary'
      default:
        return 'secondary'
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? 'Create New User Story' : 'Edit User Story'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? 'Create a new user story to track a feature or requirement.'
              : 'Update your user story details.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="As a user, I want to..."
              maxLength={200}
              disabled={isLoading}
            />
            <div className="flex justify-between">
              {errors.title && (
                <p className="text-sm text-destructive">{errors.title}</p>
              )}
              <p className="text-xs text-muted-foreground ml-auto">
                {title.length}/200
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the user story in detail..."
              rows={4}
              maxLength={1000}
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground text-right">
              {description.length}/1000
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Select
                value={priority}
                onValueChange={(value: any) => setPriority(value)}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="P0">
                    <div className="flex items-center gap-2">
                      <Badge variant="destructive">P0</Badge>
                      <span>Critical</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="P1">
                    <div className="flex items-center gap-2">
                      <Badge>P1</Badge>
                      <span>High</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="P2">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">P2</Badge>
                      <span>Normal</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select
                value={status}
                onValueChange={(value: any) => setStatus(value)}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                </SelectContent>
              </Select>
            </div>
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
              {isLoading
                ? 'Saving...'
                : mode === 'create'
                ? 'Create User Story'
                : 'Save Changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
