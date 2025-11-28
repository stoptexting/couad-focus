'use client'

import { useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { taigaApi } from '@/lib/api/taiga'
import { queryKeys } from '@/lib/queryClient'

interface VersionResponse {
  version: number
  last_sync_at: string | null
  last_webhook_at: string | null
}

/**
 * Hook for smart polling of Taiga data version.
 *
 * Polls the version endpoint every 5 seconds. When the version changes
 * (indicating a webhook was received), it invalidates Taiga queries
 * to trigger a refetch.
 *
 * @param enabled - Whether to enable polling (default: true)
 * @returns The current version data
 */
export function useTaigaVersion(enabled: boolean = true) {
  const queryClient = useQueryClient()
  const lastVersionRef = useRef<number | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.taigaVersion,
    queryFn: taigaApi.getVersion,
    refetchInterval: enabled ? 5000 : false, // Poll every 5 seconds
    refetchIntervalInBackground: true,
    staleTime: 4000,
    enabled,
  })

  useEffect(() => {
    if (data?.version !== undefined) {
      // Check if version has changed (not on initial load)
      if (lastVersionRef.current !== null && lastVersionRef.current !== data.version) {
        // Version changed - invalidate Taiga queries to trigger refetch
        queryClient.invalidateQueries({ queryKey: queryKeys.taigaTree })
        queryClient.invalidateQueries({ queryKey: queryKeys.taigaConfig })
      }
      lastVersionRef.current = data.version
    }
  }, [data?.version, queryClient])

  return {
    version: data?.version ?? 0,
    lastSyncAt: data?.last_sync_at,
    lastWebhookAt: data?.last_webhook_at,
    isLoading,
    error,
  }
}
