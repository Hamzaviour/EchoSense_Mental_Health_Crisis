import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { WORKFLOW_TABS, type WorkflowTab } from '@/types/counselor'

export default function WorkQueueTabs({
  active,
  counts,
  onChange,
}: {
  active: WorkflowTab
  counts: Record<string, number>
  onChange: (tab: WorkflowTab) => void
}) {
  return (
    <div className="flex flex-wrap gap-1.5 p-3 border-b bg-muted/20 shrink-0">
      {WORKFLOW_TABS.map(({ key, label }) => (
        <Badge
          key={key || 'all'}
          variant={active === key ? 'default' : 'outline'}
          className={cn('cursor-pointer px-3 py-1', active === key && 'shadow-sm')}
          onClick={() => onChange(key)}
        >
          {label}
          {key && counts[key] != null ? ` (${counts[key]})` : key === '' ? ` (${Object.values(counts).reduce((a, b) => a + b, 0)})` : ''}
        </Badge>
      ))}
    </div>
  )
}
