import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

function normalizeLabel(label?: string | null): string {
  return (label || 'unknown').toLowerCase().trim()
}

function sentimentClasses(label?: string | null, score?: number | null): string {
  const key = normalizeLabel(label)

  if (key.includes('positive') || key.includes('joy') || key.includes('happy')) {
    return 'border-emerald-300 bg-emerald-100 text-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-200 dark:border-emerald-800'
  }
  if (key.includes('negative') || key.includes('sad') || key.includes('fear') || key.includes('anger')) {
    return 'border-red-300 bg-red-100 text-red-900 dark:bg-red-950/60 dark:text-red-200 dark:border-red-800'
  }
  if (key.includes('neutral')) {
    return 'border-amber-300 bg-amber-100 text-amber-900 dark:bg-amber-950/60 dark:text-amber-200 dark:border-amber-800'
  }
  if (key.includes('mixed')) {
    return 'border-violet-300 bg-violet-100 text-violet-900 dark:bg-violet-950/60 dark:text-violet-200 dark:border-violet-800'
  }

  if (score != null) {
    if (score >= 0.65) {
      return 'border-red-300 bg-red-100 text-red-900 dark:bg-red-950/60 dark:text-red-200 dark:border-red-800'
    }
    if (score >= 0.4) {
      return 'border-amber-300 bg-amber-100 text-amber-900 dark:bg-amber-950/60 dark:text-amber-200 dark:border-amber-800'
    }
    return 'border-emerald-300 bg-emerald-100 text-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-200 dark:border-emerald-800'
  }

  return 'border-border bg-muted text-muted-foreground'
}

function displayLabel(label?: string | null): string {
  if (!label) return 'Unknown'
  return label.charAt(0).toUpperCase() + label.slice(1).toLowerCase()
}

export default function SentimentBadge({
  label,
  score,
  showScore = true,
  className,
}: {
  label?: string | null
  score?: number | null
  showScore?: boolean
  className?: string
}) {
  const text = displayLabel(label)
  const scoreText = score != null ? `${Math.round(score * 100)}%` : null

  return (
    <Badge
      variant="outline"
      className={cn('font-medium capitalize border', sentimentClasses(label, score), className)}
    >
      {text}
      {showScore && scoreText != null && ` · ${scoreText}`}
    </Badge>
  )
}

export { sentimentClasses, displayLabel }
