import { useCallback, useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, User, ChevronDown } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import AssessmentOffer from '@/components/AssessmentOffer'
import TypingIndicator from '@/components/chat/TypingIndicator'

export interface ChatMessage {
  id?: number
  role: string
  content: string
}

interface Offer {
  offered?: boolean
  session_id?: number
  types?: string[]
}

function groupMessages(messages: ChatMessage[]) {
  const groups: { role: string; messages: ChatMessage[] }[] = []
  messages.forEach((m) => {
    let role = 'assistant'
    if (m.role === 'PATIENT' || m.role === 'user') role = 'user'
    else if (m.role === 'COUNSELOR') role = 'counselor'
    else if (m.role === 'SYSTEM') role = 'system'
    const last = groups[groups.length - 1]
    if (last && last.role === role) last.messages.push(m)
    else groups.push({ role, messages: [m] })
  })
  return groups
}

const NEAR_BOTTOM_PX = 120

export default function ChatPanel({
  messages,
  assessmentOffer,
  typing,
  onLater,
  newMessageLabel = '↓ New messages',
}: {
  messages: ChatMessage[]
  assessmentOffer?: Offer | null
  typing?: boolean
  onLater?: () => void
  newMessageLabel?: string
}) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const isNearBottomRef = useRef(true)
  const [showNewMessages, setShowNewMessages] = useState(false)
  const groups = groupMessages(messages)

  const checkNearBottom = useCallback(() => {
    const el = scrollRef.current
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < NEAR_BOTTOM_PX
  }, [])

  const scrollToBottom = useCallback((smooth = true) => {
    bottomRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'end' })
    setShowNewMessages(false)
    isNearBottomRef.current = true
  }, [])

  const handleScroll = useCallback(() => {
    const near = checkNearBottom()
    isNearBottomRef.current = near
    if (near) setShowNewMessages(false)
  }, [checkNearBottom])

  useEffect(() => {
    if (isNearBottomRef.current) {
      scrollToBottom(messages.length <= 2 ? false : true)
    } else {
      setShowNewMessages(true)
    }
  }, [messages, typing, scrollToBottom])

  return (
    <div className="relative flex flex-1 min-h-0 flex-col">
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 min-h-0 overflow-y-auto overscroll-contain"
      >
        <div className="px-4 py-6 space-y-6 max-w-3xl mx-auto">
          <AnimatePresence initial={false}>
            {groups.map((group, gi) => {
              const isUser = group.role === 'user'
              const isCounselor = group.role === 'counselor'
              const isSystem = group.role === 'system'
              const isLastAssistant = !isUser && !isSystem && gi === groups.length - 1
              return (
                <motion.div
                  key={gi}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, ease: 'easeOut' }}
                  className={cn('flex gap-3', isUser && 'flex-row-reverse', isSystem && 'justify-center')}
                >
                  {!isSystem && (
                  <Avatar className="h-8 w-8 mt-1 shrink-0">
                    <AvatarFallback
                      className={
                        isUser
                          ? 'bg-calm-600 text-white'
                          : isCounselor
                            ? 'bg-indigo-600 text-white'
                            : 'bg-secondary text-secondary-foreground'
                      }
                    >
                      {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </AvatarFallback>
                  </Avatar>
                  )}
                  <div className={cn('flex flex-col gap-1 max-w-[80%]', isUser && 'items-end', isSystem && 'max-w-full items-center')}>
                    {group.messages.map((m, mi) => (
                      <div
                        key={m.id || mi}
                        className={cn(
                          'rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm',
                          isSystem
                            ? 'bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-100 text-center text-xs'
                            : isUser
                            ? 'bg-primary text-primary-foreground rounded-br-md'
                            : isCounselor
                              ? 'bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 rounded-bl-md'
                              : 'bg-card border border-border/60 rounded-bl-md'
                        )}
                      >
                        {m.content}
                      </div>
                    ))}
                    {isLastAssistant && assessmentOffer && (
                      <AssessmentOffer offer={assessmentOffer} onLater={onLater} />
                    )}
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
          {typing && <TypingIndicator />}
          <div ref={bottomRef} className="h-px shrink-0" aria-hidden />
        </div>
      </div>

      {showNewMessages && (
        <Button
          size="sm"
          variant="secondary"
          className="absolute bottom-4 left-1/2 -translate-x-1/2 shadow-md gap-1 z-10"
          onClick={() => scrollToBottom(true)}
        >
          <ChevronDown className="h-4 w-4" />
          {newMessageLabel}
        </Button>
      )}
    </div>
  )
}
