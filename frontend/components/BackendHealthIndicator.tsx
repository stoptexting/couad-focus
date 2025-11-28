'use client'

import { useQuery } from '@tanstack/react-query'
import { healthApi } from '@/lib/api/health'
import { Activity, AlertCircle, Wifi, WifiOff } from 'lucide-react'

export function BackendHealthIndicator() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['backend-health'],
    queryFn: healthApi.check,
    refetchInterval: 5000, // Poll every 5 seconds
    retry: 1,
    retryDelay: 1000,
  })

  const getStatus = () => {
    if (isLoading) return 'checking'
    if (isError || data?.status !== 'ok') return 'error'
    return 'healthy'
  }

  const status = getStatus()

  const statusConfig = {
    healthy: {
      color: 'bg-green-500',
      icon: Wifi,
      text: 'Backend Connected',
      dotColor: 'bg-green-400',
    },
    error: {
      color: 'bg-red-500',
      icon: WifiOff,
      text: 'Backend Disconnected',
      dotColor: 'bg-red-400',
    },
    checking: {
      color: 'bg-yellow-500',
      icon: Activity,
      text: 'Checking Connection...',
      dotColor: 'bg-yellow-400',
    },
  }

  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <div className="flex items-center gap-2 group relative">
      {/* Status indicator dot */}
      <div className="relative flex items-center">
        <div className={`h-2 w-2 rounded-full ${config.dotColor}`}>
          {status === 'healthy' && (
            <div className={`absolute inset-0 rounded-full ${config.dotColor} animate-ping`} />
          )}
        </div>
      </div>

      {/* Icon (visible on hover) */}
      <Icon className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Tooltip */}
      <div className="absolute right-0 top-full mt-2 px-3 py-2 bg-popover text-popover-foreground text-sm rounded-md shadow-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 border">
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${config.color}`} />
          <span>{config.text}</span>
        </div>
        {data?.timestamp && status === 'healthy' && (
          <div className="text-xs text-muted-foreground mt-1">
            Last check: {new Date(data.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  )
}
