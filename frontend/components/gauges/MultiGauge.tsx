'use client'

import { GaugeData, LayoutType } from '@/lib/types'
import { Gauge } from './Gauge'
import { cn } from '@/lib/utils'

interface MultiGaugeProps {
  gauges: GaugeData[]
  layout: LayoutType
  className?: string
}

export function MultiGauge({ gauges, layout, className }: MultiGaugeProps) {
  if (layout === 'single') {
    return (
      <div className={cn('flex justify-center items-center', className)}>
        {gauges.length > 0 && <Gauge data={gauges[0]} size="xl" />}
      </div>
    )
  }

  const gridCols = layout === 'sprint_view'
    ? 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
    : 'grid-cols-3 md:grid-cols-4 lg:grid-cols-6'

  return (
    <div className={cn('grid gap-6', gridCols, className)}>
      {gauges.map((gauge) => (
        <Gauge key={gauge.id} data={gauge} size={layout === 'sprint_view' ? 'lg' : 'md'} />
      ))}
    </div>
  )
}
