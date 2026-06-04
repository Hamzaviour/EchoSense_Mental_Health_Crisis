import { useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { cn } from '@/lib/utils'
import SidebarNav from '@/components/layout/SidebarNav'
import { Button } from '@/components/ui/button'
import { useState } from 'react'

export default function AppShell({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { pathname } = useLocation()

  return (
    <div className={cn('h-screen flex overflow-hidden bg-background', className)}>
      <SidebarNav />
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            aria-label="Close menu"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 bottom-0 w-64 bg-card shadow-xl flex flex-col">
            <SidebarNav compact />
          </div>
        </div>
      )}
      <div className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden">
        <header className="md:hidden border-b bg-card px-4 py-3 flex items-center justify-between shrink-0">
          <Button variant="ghost" size="icon" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </Button>
          <span className="text-sm font-medium truncate capitalize">
            {pathname.split('/').filter(Boolean)[0]?.replace('-', ' ') || 'Echo Sense'}
          </span>
          <div className="w-9" />
        </header>
        <main className="flex-1 flex flex-col min-h-0 overflow-hidden">{children}</main>
      </div>
    </div>
  )
}
