import { cn } from '@/lib/utils'
import SentimentBadge from '@/components/SentimentBadge'
import type { TriagePatient } from '@/types/counselor'

export default function PatientTriageCard({
  patient,
  selected,
  onClick,
}: {
  patient: TriagePatient
  selected?: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full text-left rounded-lg border p-3 transition-all hover:shadow-md',
        'bg-card hover:border-primary/40',
        selected && 'ring-2 ring-primary border-primary/50 shadow-md'
      )}
    >
      <div className="flex justify-between items-start gap-2 mb-2">
        <div className="min-w-0">
          <p className="font-medium text-sm truncate">{patient.full_name}</p>
          <p className="text-[10px] text-muted-foreground">{patient.patient_id}</p>
        </div>
        <span className="text-xs font-mono font-semibold text-primary shrink-0">
          {Math.round(patient.latest_risk_score)}
        </span>
      </div>
      {(patient.sentiment_label || patient.sentiment_score != null) && (
        <div className="mb-2">
          <SentimentBadge
            label={patient.sentiment_label}
            score={patient.sentiment_score}
            className="text-[10px] py-0 h-5"
          />
        </div>
      )}
      {patient.last_message && (
        <p className="text-xs text-muted-foreground line-clamp-2 mb-2 italic">
          &ldquo;{patient.last_message.content}&rdquo;
        </p>
      )}
      <p className="text-[10px] text-primary/80 mb-1">{patient.assessment_status.label}</p>
      <div className="flex justify-between items-center text-[10px] text-muted-foreground">
        <span>{patient.time_since_activity || 'No activity'}</span>
        <span className="uppercase tracking-wide">{patient.workflow_status.replace('_', ' ')}</span>
      </div>
    </button>
  )
}
