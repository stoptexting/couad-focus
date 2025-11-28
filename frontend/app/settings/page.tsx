'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Settings, Database, AlertTriangle, RefreshCw, Webhook, Copy, Check, X, History } from 'lucide-react'
import { adminApi } from '@/lib/api/admin'
import { taigaApi } from '@/lib/api/taiga'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useToast } from '@/hooks/use-toast'
import { queryKeys } from '@/lib/queryClient'

export default function SettingsPage() {
  const [showResetDialog, setShowResetDialog] = useState(false)
  const [webhookSecret, setWebhookSecret] = useState('')
  const [copiedUrl, setCopiedUrl] = useState(false)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  // Get current Taiga config to check webhook status
  const { data: taigaConfig } = useQuery({
    queryKey: queryKeys.taigaConfig,
    queryFn: taigaApi.getConfig,
  })

  const webhookUrl = typeof window !== 'undefined'
    ? `${window.location.origin}/api/taiga/webhook`
    : '/api/taiga/webhook'

  const setWebhookMutation = useMutation({
    mutationFn: taigaApi.setWebhookConfig,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaConfig })
      toast({
        title: 'Webhook Configured',
        description: 'Webhook secret has been set successfully.',
      })
      setWebhookSecret('')
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to Set Webhook',
        description: error.response?.data?.error || 'Failed to configure webhook.',
        variant: 'destructive',
      })
    },
  })

  const clearWebhookMutation = useMutation({
    mutationFn: taigaApi.clearWebhookConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.taigaConfig })
      toast({
        title: 'Webhook Disabled',
        description: 'Webhook configuration has been cleared.',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to Clear Webhook',
        description: error.response?.data?.error || 'Failed to clear webhook configuration.',
        variant: 'destructive',
      })
    },
  })

  const handleSetWebhook = () => {
    if (webhookSecret.length < 8) {
      toast({
        title: 'Invalid Secret',
        description: 'Webhook secret must be at least 8 characters.',
        variant: 'destructive',
      })
      return
    }
    setWebhookMutation.mutate(webhookSecret)
  }

  const copyWebhookUrl = async () => {
    await navigator.clipboard.writeText(webhookUrl)
    setCopiedUrl(true)
    setTimeout(() => setCopiedUrl(false), 2000)
  }

  const resetMutation = useMutation({
    mutationFn: adminApi.resetDatabase,
    onSuccess: (data) => {
      // Invalidate all queries to force refetch
      queryClient.invalidateQueries()

      toast({
        title: 'Database Cleared',
        description: `Deleted ${data.data.projects} projects, ${data.data.sprints} sprints, ${data.data.user_stories} user stories, and ${data.data.tasks} tasks.`,
        variant: 'default',
      })

      setShowResetDialog(false)
    },
    onError: (error: any) => {
      toast({
        title: 'Reset Failed',
        description: error.response?.data?.message || 'Failed to reset database. Please try again.',
        variant: 'destructive',
      })

      setShowResetDialog(false)
    },
  })

  const handleReset = () => {
    resetMutation.mutate()
  }

  return (
    <div className="container mx-auto p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold flex items-center gap-3">
            <Settings className="h-10 w-10" />
            Settings
          </h1>
          <p className="text-muted-foreground mt-2">
            Manage application settings and data
          </p>
        </div>
      </div>

      <div className="max-w-3xl space-y-6">
        {/* Database Management Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Database Management
            </CardTitle>
            <CardDescription>
              Reset and manage your application data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-destructive mb-1">
                    Reset Database
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    This will permanently delete all projects, sprints, user stories, and tasks.
                    You will need to fetch your projects again from Taiga. This action cannot be undone.
                  </p>
                  <Button
                    variant="destructive"
                    onClick={() => setShowResetDialog(true)}
                    disabled={resetMutation.isPending}
                    className="gap-2"
                  >
                    {resetMutation.isPending ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        Resetting...
                      </>
                    ) : (
                      <>
                        <Database className="h-4 w-4" />
                        Reset Database
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Webhook Configuration Section - COMING SOON */}
        <Card className="opacity-60">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Webhook className="h-5 w-5" />
                Webhook Configuration
              </CardTitle>
              <span className="text-xs font-medium bg-muted px-2 py-1 rounded">
                Coming Soon
              </span>
            </div>
            <CardDescription>
              Configure Taiga webhooks for real-time sync updates
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pointer-events-none">
            {/* Webhook Status */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Status:</span>
              {taigaConfig?.webhook_configured ? (
                <span className="inline-flex items-center gap-1 text-sm text-green-600 dark:text-green-400">
                  <Check className="h-4 w-4" />
                  Enabled
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-sm text-muted-foreground">
                  <X className="h-4 w-4" />
                  Disabled
                </span>
              )}
              {taigaConfig?.last_webhook_at && (
                <span className="text-sm text-muted-foreground ml-2">
                  (Last received: {new Date(taigaConfig.last_webhook_at).toLocaleString()})
                </span>
              )}
            </div>

            {/* Webhook URL */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Webhook URL</label>
              <div className="flex gap-2">
                <Input
                  readOnly
                  value={webhookUrl}
                  className="font-mono text-sm"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={copyWebhookUrl}
                  title="Copy webhook URL"
                >
                  {copiedUrl ? (
                    <Check className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Use this URL when configuring webhooks in Taiga project settings.
              </p>
            </div>

            {/* Set Webhook Secret */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Webhook Secret</label>
              <div className="flex gap-2">
                <Input
                  type="password"
                  placeholder="Enter webhook secret (min 8 characters)"
                  value={webhookSecret}
                  onChange={(e) => setWebhookSecret(e.target.value)}
                  className="font-mono"
                />
                <Button
                  onClick={handleSetWebhook}
                  disabled={setWebhookMutation.isPending || webhookSecret.length < 8}
                >
                  {setWebhookMutation.isPending ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    'Set Secret'
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                This secret must match the one configured in Taiga for signature verification.
              </p>
            </div>

            {/* Clear Webhook */}
            {taigaConfig?.webhook_configured && (
              <div className="pt-2 border-t">
                <Button
                  variant="outline"
                  onClick={() => clearWebhookMutation.mutate()}
                  disabled={clearWebhookMutation.isPending}
                  className="text-destructive hover:text-destructive"
                >
                  {clearWebhookMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                      Disabling...
                    </>
                  ) : (
                    'Disable Webhook'
                  )}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Webhook History Section - COMING SOON */}
        <Card className="opacity-60">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Webhook History
              </CardTitle>
              <span className="text-xs font-medium bg-muted px-2 py-1 rounded">
                Coming Soon
              </span>
            </div>
            <CardDescription>
              Latest 5 webhooks received from Taiga
            </CardDescription>
          </CardHeader>
          <CardContent className="pointer-events-none">
            {taigaConfig?.webhook_history && taigaConfig.webhook_history.length > 0 ? (
              <div className="space-y-3">
                {taigaConfig.webhook_history.map((entry, idx) => (
                  <div key={idx} className="border rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {entry.success ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <X className="h-4 w-4 text-destructive" />
                        )}
                        <span className="font-mono text-xs uppercase bg-muted px-1.5 py-0.5 rounded">
                          {entry.action}
                        </span>
                        <span className="text-muted-foreground">
                          {entry.entity_type}
                        </span>
                        {entry.entity_name && (
                          <span className="truncate max-w-[150px]" title={entry.entity_name}>
                            {entry.entity_name}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {new Date(entry.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <details className="text-xs">
                      <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                        View payload
                      </summary>
                      <pre className="mt-2 p-2 bg-muted rounded overflow-x-auto max-h-32 text-xs">
                        {JSON.stringify(entry.payload, null, 2)}
                      </pre>
                    </details>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No webhooks received yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Confirmation Dialog */}
      <AlertDialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Are you absolutely sure?
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>
                This action will permanently delete all your current data including:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>All projects and their configurations</li>
                <li>All sprints and their timelines</li>
                <li>All user stories and their details</li>
                <li>All tasks and their statuses</li>
              </ul>
              <p className="font-semibold mt-3">
                You will need to fetch your projects again from Taiga.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={resetMutation.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleReset}
              disabled={resetMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {resetMutation.isPending ? 'Resetting...' : 'Reset Database'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
