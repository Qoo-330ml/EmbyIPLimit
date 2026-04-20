import { useEffect, useMemo, useRef, useState } from 'react'
import { Play } from 'lucide-react'
import { apiRequest } from '@/types/api'
import { Card, CardContent } from '@/components/ui/card'

export function useActiveSessions(pollInterval = 5000) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const fingerprintRef = useRef('')

  useEffect(() => {
    let active = true
    let timer = null

    const load = async (showLoading = false) => {
      if (!active) return
      if (showLoading) setLoading(true)
      try {
        const data = await apiRequest('/public/active-sessions')
        const next = (data.sessions || []).slice().sort((a, b) =>
          String(a.session_id).localeCompare(String(b.session_id))
        )
        const fingerprint = JSON.stringify(
          next.map((s) => ({
            session_id: s.session_id,
            user_id: s.user_id,
            username: s.username,
            ip_address: s.ip_address,
            media: s.media || s.media_name,
            device: s.device || s.device_name,
            client: s.client || s.client_type,
            location: s.location,
          }))
        )
        if (active && fingerprint !== fingerprintRef.current) {
          setSessions(next)
          fingerprintRef.current = fingerprint
        }
      } catch {
        if (active && showLoading) {
          setSessions([])
          fingerprintRef.current = ''
        }
      } finally {
        if (active && showLoading) setLoading(false)
      }
    }

    load(true)
    timer = setInterval(() => load(false), pollInterval)

    return () => {
      active = false
      if (timer) clearInterval(timer)
    }
  }, [pollInterval])

  const sessionCountText = useMemo(() => `当前正在播放（${sessions.length}）`, [sessions.length])

  return { sessions, loading, sessionCountText }
}

export function ActiveSessionCard({ session }) {
  const mediaName = session.media || session.media_name
  const deviceName = session.device || session.device_name
  const clientType = session.client || session.client_type

  return (
    <Card className='overflow-hidden transition-all hover:shadow-md'>
      <CardContent className='p-4'>
        <div className='flex items-start gap-3'>
          <div className='relative flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary/10'>
            <div className='absolute inset-0 rounded-xl bg-gradient-to-br from-primary/10 to-transparent' />
            <Play className='relative z-10 h-6 w-6 text-primary' />
          </div>
          <div className='flex-1 min-w-0'>
            <div className='font-medium'>{session.username}</div>
            <div className='mt-1 text-sm text-muted-foreground truncate'>{mediaName}</div>
            <div className='mt-2 flex items-center gap-2 text-xs text-muted-foreground'>
              <span className='truncate'>{deviceName}</span>
              <span>·</span>
              <span className='truncate'>{clientType}</span>
            </div>
          </div>
        </div>
        <div className='mt-3 border-t border-border' />
        <div className='mt-3 flex justify-between gap-2 text-xs'>
          <span className='text-muted-foreground shrink-0'>IP: {session.ip_address}</span>
          <span className='text-primary truncate'>{session.location}</span>
        </div>
      </CardContent>
    </Card>
  )
}
