'use client'

import { GaugeData } from '@/lib/types'
import { cn } from '@/lib/utils'

interface GaugeProps {
  data: GaugeData
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

const sizeMap = {
  sm: { height: 'h-32', width: 'w-4', text: 'text-xs' },
  md: { height: 'h-48', width: 'w-6', text: 'text-sm' },
  lg: { height: 'h-64', width: 'w-8', text: 'text-base' },
  xl: { height: 'h-96', width: 'w-12', text: 'text-lg' },
}

const getColorClasses = (type?: 'project' | 'sprint' | 'user_story') => {
  switch (type) {
    case 'project':
      return 'bg-blue-500'
    case 'sprint':
      return 'bg-green-500'
    case 'user_story':
      return 'bg-yellow-500'
    default:
      return 'bg-blue-500'
  }
}

export function Gauge({ data, size = 'md', className }: GaugeProps) {
  const { label, percentage, color, type, segments } = data
  const sizeClasses = sizeMap[size]

  // Render segments (multi-color for sprint view, single color otherwise)
  const renderFill = () => {
    // Multi-segment display when segments are provided
    if (segments && segments.length > 0) {
      const totalContribution = segments.reduce((sum, s) => sum + s.percentage, 0)
      if (totalContribution === 0) return null

      let currentBottom = 0
      return segments.map((segment, i) => {
        const segmentHeight = (segment.percentage / totalContribution) * percentage
        const bottom = currentBottom
        currentBottom += segmentHeight

        return (
          <div
            key={i}
            className="absolute w-full transition-all duration-300"
            style={{
              bottom: `${bottom}%`,
              height: `${segmentHeight}%`,
              backgroundColor: segment.color,
            }}
          />
        )
      })
    }

    // Single color fallback
    const colorClasses = color ? '' : getColorClasses(type)
    return (
      <div
        className={cn('absolute bottom-0 w-full transition-all duration-300', colorClasses)}
        style={{
          height: `${Math.max(0, Math.min(100, percentage))}%`,
          backgroundColor: color || undefined,
        }}
      />
    )
  }

  return (
    <div className={cn('flex flex-col items-center gap-2', className)}>
      <div className={cn('relative bg-gray-200 dark:bg-gray-800 rounded-sm overflow-hidden', sizeClasses.height, sizeClasses.width)}>
        {renderFill()}
      </div>
      <div className="flex flex-col items-center gap-1">
        <span className={cn('font-medium text-center', sizeClasses.text)}>{label}</span>
        <span className={cn('text-gray-600 dark:text-gray-400', sizeClasses.text)}>
          {Math.round(percentage)}%
        </span>
      </div>
    </div>
  )
}
