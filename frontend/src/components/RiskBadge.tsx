import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const variantMap: Record<string, 'low' | 'moderate' | 'high' | 'critical'> = {
  Low: 'low',
  Moderate: 'moderate',
  High: 'high',
  Critical: 'critical',
}

export default function RiskBadge({ level, score }: { level?: string; score?: number }) {
  const v = level ? variantMap[level] : undefined
  return (
    <Badge variant={v || 'default'} className={cn('font-normal')}>
      {score != null ? `${level} · ${Math.round(score)}` : level}
    </Badge>
  )
}
