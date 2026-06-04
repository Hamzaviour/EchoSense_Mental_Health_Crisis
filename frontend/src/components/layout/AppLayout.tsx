import AppShell from '@/components/layout/AppShell'
import { cn } from '@/lib/utils'

/** Patient layout — sidebar nav is role-aware via SidebarNav */
export default function AppLayout({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return <AppShell className={cn(className)}>{children}</AppShell>
}
