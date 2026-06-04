import { ScrollArea } from '@/components/ui/scroll-area'
import { RISK_COLUMNS, type TriagePatient } from '@/types/counselor'
import PatientTriageCard from './PatientTriageCard'

export default function TriageBoard({
  columns,
  selectedId,
  onSelect,
}: {
  columns: Record<string, TriagePatient[]>
  selectedId?: number
  onSelect: (p: TriagePatient) => void
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 min-h-0 flex-1 p-3 overflow-hidden">
      {RISK_COLUMNS.map(({ key, label, emoji, color }) => (
        <div key={key} className={`flex flex-col rounded-xl border min-h-0 ${color}`}>
          <div className="px-3 py-2 border-b border-inherit shrink-0 flex justify-between items-center">
            <span className="text-xs font-semibold">
              {emoji} {label}
            </span>
            <span className="text-[10px] text-muted-foreground">{(columns[key] || []).length}</span>
          </div>
          <ScrollArea className="flex-1 min-h-[200px] max-h-[calc(100vh-16rem)]">
            <div className="p-2 space-y-2">
              {(columns[key] || []).length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-6">No patients</p>
              )}
              {(columns[key] || []).map((p) => (
                <PatientTriageCard
                  key={p.id}
                  patient={p}
                  selected={selectedId === p.id}
                  onClick={() => onSelect(p)}
                />
              ))}
            </div>
          </ScrollArea>
        </div>
      ))}
    </div>
  )
}
