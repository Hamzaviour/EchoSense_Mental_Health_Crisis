import type { LucideIcon } from 'lucide-react'
import {
  BarChart3,
  FileText,
  Heart,
  LayoutDashboard,
  Leaf,
  MessageCircle,
  MessageSquare,
  Shield,
  Sparkles,
  Users,
} from 'lucide-react'

export type NavItem = {
  to: string
  label: string
  icon: LucideIcon
  roles: Array<'PATIENT' | 'COUNSELOR' | 'ADMIN'>
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/chat', label: 'Chat', icon: MessageCircle, roles: ['PATIENT'] },
  { to: '/therapy-plan', label: 'Therapy Plan', icon: Sparkles, roles: ['PATIENT'] },
  { to: '/coping-tools', label: 'Coping Tools', icon: Leaf, roles: ['PATIENT'] },
  { to: '/counselor/triage', label: 'Live Triage', icon: LayoutDashboard, roles: ['COUNSELOR', 'ADMIN'] },
  { to: '/counselor/decision', label: 'Decision Workspace', icon: FileText, roles: ['COUNSELOR', 'ADMIN'] },
  { to: '/counselor/chat-support', label: 'Chat Support', icon: MessageSquare, roles: ['COUNSELOR', 'ADMIN'] },
  { to: '/counselor/navigator', label: 'Patient Navigator', icon: Users, roles: ['COUNSELOR', 'ADMIN'] },
  { to: '/admin', label: 'Analytics', icon: BarChart3, roles: ['COUNSELOR'] },
  { to: '/admin', label: 'Admin Console', icon: Shield, roles: ['ADMIN'] },
]

export function navForRole(role: string | undefined): NavItem[] {
  if (!role) return []
  return NAV_ITEMS.filter((item) => item.roles.includes(role as NavItem['roles'][number]))
}

export function homeRouteForRole(role: string | undefined): string {
  switch (role) {
    case 'PATIENT':
      return '/chat'
    case 'COUNSELOR':
    case 'ADMIN':
      return '/counselor/triage'
    default:
      return '/login'
  }
}

export const ROLE_LABELS: Record<string, string> = {
  PATIENT: 'Patient',
  COUNSELOR: 'Counselor',
  ADMIN: 'Administrator',
}

export { Heart }
