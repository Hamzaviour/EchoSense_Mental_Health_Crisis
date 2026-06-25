import { Link, useLocation, useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import ThemeToggle from '@/components/ThemeToggle'
import LanguageToggle from '@/components/LanguageToggle'
import { useAuth } from '@/context/AuthContext'
import { useLanguage } from '@/context/LanguageContext'
import { Heart, homeRouteForRole, navForRole, ROLE_LABELS } from '@/config/navigation'

export default function SidebarNav({ compact }: { compact?: boolean }) {
  const { pathname } = useLocation()
  const { user, profile, logout } = useAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const role = user?.role
  const items = navForRole(role)
  const home = homeRouteForRole(role)
  const displayName =
    (profile?.full_name as string) || user?.email?.split('@')[0] || 'User'

  const patientLinks = [
    { to: '/chat', label: t.nav.chat },
    { to: '/journal', label: t.nav.journal },
    { to: '/session-request', label: t.nav.sessionRequest },
    { to: '/therapy-plan', label: t.nav.therapyPlan },
    { to: '/coping-tools', label: t.nav.copingTools },
  ]

  const resolvedItems =
    role === 'PATIENT'
      ? items.map((item) => {
          const translated = patientLinks.find((p) => p.to === item.to)
          return translated ? { ...item, label: translated.label } : item
        })
      : items

  return (
    <aside
      className={cn(
        'flex flex-col border-r bg-card shrink-0',
        compact ? 'w-full border-r-0 border-b' : 'hidden md:flex w-56'
      )}
    >
      <Link to={home} className="p-4 flex items-center gap-2 border-b hover:bg-muted/30 transition-colors">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
          <Heart className="h-4 w-4 text-primary" />
        </span>
        <div className="min-w-0">
          <span className="font-semibold text-calm-900 dark:text-calm-100 block truncate">Echo Sense</span>
          {!compact && role && (
            <span className="text-[10px] text-muted-foreground">{ROLE_LABELS[role] || role}</span>
          )}
        </div>
      </Link>

      <nav className="flex-1 p-3 space-y-1">
        {resolvedItems.map(({ to, label, icon: Icon }) => {
          const active =
            pathname === to || (to === '/counselor/triage' && pathname === '/counselor')
          return (
            <Link
              key={`${role}-${to}-${label}`}
              to={to}
              className={cn(
                'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors',
                active
                  ? 'bg-primary/10 text-calm-800 dark:text-calm-100 font-medium'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{label}</span>
            </Link>
          )
        })}
      </nav>

      <div className="p-3 border-t space-y-2">
        {!compact && (
          <div className="px-2 py-1.5 rounded-lg bg-muted/40 space-y-1">
            <p className="text-xs font-medium truncate">{displayName}</p>
            <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
            {role && (
              <Badge variant="outline" className="text-[10px] py-0 h-5">
                {ROLE_LABELS[role]}
              </Badge>
            )}
          </div>
        )}
        <div className="flex flex-col gap-2">
          {role === 'PATIENT' && <LanguageToggle className="w-full justify-center" />}
          <ThemeToggle className="w-full justify-center" />
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start"
          onClick={() => {
            logout()
            navigate('/login')
          }}
        >
          <LogOut className="h-4 w-4 mr-2" />
          {t.nav.logout}
        </Button>
      </div>
    </aside>
  )
}
