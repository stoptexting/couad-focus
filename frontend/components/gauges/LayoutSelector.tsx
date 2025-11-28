'use client'

import { LayoutType } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface LayoutSelectorProps {
  currentLayout: LayoutType
  onLayoutChange: (layout: LayoutType) => void
  className?: string
}

const layouts: { value: LayoutType; label: string; description: string }[] = [
  {
    value: 'single',
    label: 'Single',
    description: 'One gauge for entire project',
  },
  {
    value: 'sprint_view',
    label: 'Sprint View',
    description: 'One gauge per sprint',
  },
  {
    value: 'user_story_layout',
    label: 'User Story Layout',
    description: 'Sprint + all user stories',
  },
]

export function LayoutSelector({ currentLayout, onLayoutChange, className }: LayoutSelectorProps) {
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {layouts.map((layout) => (
        <Button
          key={layout.value}
          variant={currentLayout === layout.value ? 'default' : 'outline'}
          size="sm"
          onClick={() => onLayoutChange(layout.value)}
          title={layout.description}
          className="flex-1 min-w-[120px]"
        >
          {layout.label}
        </Button>
      ))}
    </div>
  )
}
