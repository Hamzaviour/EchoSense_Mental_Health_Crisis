export interface TriagePatient {
  id: number
  patient_id: string
  full_name: string
  latest_risk_score: number
  latest_risk_level: string
  sentiment_score?: number | null
  sentiment_label?: string | null
  last_message?: { content: string; role: string; at?: string } | null
  assessment_status: {
    phq9_done: boolean
    gad7_done: boolean
    who5_done: boolean
    phq9_score?: number | null
    gad7_score?: number | null
    label: string
  }
  time_since_activity?: string | null
  workflow_status: string
  follow_up_at?: string | null
  session_scheduled_at?: string | null
  escalation_status?: string | null
  escalation_id?: number | null
}

export type WorkflowTab = 'NEW' | 'IN_PROGRESS' | 'FOLLOW_UP' | 'ESCALATED' | 'RESOLVED' | ''

export const RISK_COLUMNS = [
  { key: 'Low', label: 'Low Risk', emoji: '🟢', color: 'border-emerald-200 bg-emerald-50/50 dark:bg-emerald-950/20' },
  { key: 'Moderate', label: 'Moderate', emoji: '🟡', color: 'border-amber-200 bg-amber-50/50 dark:bg-amber-950/20' },
  { key: 'High', label: 'High Risk', emoji: '🔴', color: 'border-orange-200 bg-orange-50/50 dark:bg-orange-950/20' },
  { key: 'Critical', label: 'Critical', emoji: '⚫', color: 'border-slate-400 bg-slate-100/80 dark:bg-slate-900/40' },
] as const

export const WORKFLOW_TABS = [
  { key: '' as WorkflowTab, label: 'All Patients' },
  { key: 'NEW' as WorkflowTab, label: 'New Patients' },
  { key: 'IN_PROGRESS' as WorkflowTab, label: 'In Progress' },
  { key: 'FOLLOW_UP' as WorkflowTab, label: 'Waiting Follow-up' },
  { key: 'ESCALATED' as WorkflowTab, label: 'Escalated Cases' },
  { key: 'RESOLVED' as WorkflowTab, label: 'Resolved' },
]
