import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import SidebarNav from '@/components/layout/SidebarNav'
import NotificationBell from '@/components/counselor/NotificationBell'
import { Button } from '@/components/ui/button'

export default function CounselorLayout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { pathname } = useLocation()

  const pageTitle = pathname.includes('admin')
    ? 'Admin Console'
    : pathname.includes('navigator')
      ? 'Patient Navigator'
      : pathname.includes('decision')
        ? 'Decision Workspace'
        : pathname.includes('chat-support')
          ? 'Chat Support'
          : 'Live Triage'

  return (
    <div className="h-screen flex overflow-hidden bg-muted/30">
      <SidebarNav />
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            aria-label="Close menu"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 bottom-0 w-64 bg-card shadow-xl">
            <SidebarNav compact />
          </div>
        </div>
      )}
      <div className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden">
        <header className="border-b bg-card px-4 py-2.5 flex items-center justify-between shrink-0 gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <Button variant="ghost" size="icon" className="md:hidden shrink-0" onClick={() => setMobileOpen(true)} aria-label="Open menu">
              <Menu className="h-5 w-5" />
            </Button>
            <span className="text-sm font-medium truncate hidden md:inline text-muted-foreground">Echo Sense</span>
            <span className="text-muted-foreground hidden md:inline">·</span>
            <span className="text-sm font-semibold truncate">{pageTitle}</span>
          </div>
          <NotificationBell />
        </header>
        {children}
      </div>
    </div>
  )
}
