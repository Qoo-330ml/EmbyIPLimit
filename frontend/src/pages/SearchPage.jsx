import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiRequest } from '@/types/api'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import UserIdentity from '@/components/UserIdentity'
import { formatDuration } from '@/types/format'

export default function SearchPage() {
  const [searchParams] = useSearchParams()
  const username = searchParams.get('username')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!username) return
    setLoading(true)
    apiRequest(`/public/search?username=${encodeURIComponent(username)}`)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [username])

  return (
    <>
      <Header>
        <h1 className='text-lg font-medium'>用户搜索</h1>
      </Header>
      <Main>
        {loading ? (
          <div className='text-muted-foreground'>搜索中...</div>
        ) : error ? (
          <Card>
            <CardContent className='pt-6'>
              <p className='text-destructive'>{error}</p>
            </CardContent>
          </Card>
        ) : data ? (
          <div className='grid gap-4'>
            <Card>
              <CardHeader>
                <CardTitle>用户信息</CardTitle>
                <CardDescription>搜索: {username}</CardDescription>
              </CardHeader>
              <CardContent>
                <UserIdentity name={data.username || username} groups={data.user_groups || []} />
                {data.user?.is_disabled && <Badge variant='destructive' className='mt-2'>已禁用</Badge>}
              </CardContent>
            </Card>
            {data.active_sessions?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>正在播放</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className='grid gap-2'>
                    {data.active_sessions.map((s, i) => (
                      <div key={i} className='rounded-lg border p-3'>
                        <div className='font-medium'>{s.media_name || '未知内容'}</div>
                        <div className='text-xs text-muted-foreground'>{s.client_type || '-'} · {s.device_name || '-'}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            {data.recent_plays?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>最近播放</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className='grid gap-2'>
                    {data.recent_plays.map((r, i) => (
                      <div key={i} className='flex items-center justify-between rounded-lg border p-3'>
                        <span className='text-sm truncate'>{r.title}</span>
                        <span className='text-xs text-muted-foreground shrink-0'>{formatDuration(r.duration)}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        ) : null}
      </Main>
    </>
  )
}
