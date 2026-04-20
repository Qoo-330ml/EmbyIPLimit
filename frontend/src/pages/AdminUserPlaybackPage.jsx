import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Play, ShieldAlert, Clock, Monitor, Globe } from 'lucide-react'
import { apiRequest } from '@/types/api'
import { formatDuration } from '@/types/format'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import UserIdentity from '@/components/UserIdentity'

export default function AdminUserPlaybackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const username = searchParams.get('username')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!username) return
    setLoading(true)
    apiRequest(`/public/search?username=${encodeURIComponent(username)}`)
      .then((result) => {
        setData(result)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [username])

  const userInfo = data?.user_info || {}
  const policy = userInfo?.Policy || {}
  const lastActivityDate = userInfo?.LastActivityDate || userInfo?.LastLoginDate || ''
  const isDisabled = policy.IsDisabled || false
  const maxSessions = policy.MaxActiveSessions ?? null
  const remoteClientBitrateLimit = policy.RemoteClientBitrateLimit ?? null

  return (
    <>
      <Header>
        <div className='flex items-center gap-4'>
          <Button variant='ghost' size='sm' onClick={() => navigate(-1)}>
            <ArrowLeft className='size-4 mr-1' />
            返回
          </Button>
          <h1 className='text-lg font-medium'>{username ? `${username} 的播放记录` : '用户播放记录'}</h1>
        </div>
      </Header>
      <Main>
        {loading ? (
          <div className='text-muted-foreground'>加载中...</div>
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
                <CardDescription>{username}</CardDescription>
              </CardHeader>
              <CardContent className='space-y-4'>
                <div className='flex flex-wrap items-center gap-2'>
                  <UserIdentity name={username} groups={data.user_groups || []} />
                  {isDisabled && <Badge variant='destructive'>已禁用</Badge>}
                  {data.ban_info?.action && <Badge variant='destructive'><ShieldAlert className='mr-1 h-3 w-3' />已封禁</Badge>}
                </div>

                <div className='grid gap-3 sm:grid-cols-2 lg:grid-cols-3'>
                  {data.user_id && (
                    <div className='flex items-center gap-2 text-sm'>
                      <span className='text-muted-foreground'>用户ID:</span>
                      <span className='font-mono text-xs'>{data.user_id}</span>
                    </div>
                  )}
                  {lastActivityDate && (
                    <div className='flex items-center gap-2 text-sm'>
                      <Clock className='h-4 w-4 text-muted-foreground' />
                      <span className='text-muted-foreground'>最后活动:</span>
                      <span>{new Date(lastActivityDate.replace(' ', 'T')).toLocaleString('zh-CN')}</span>
                    </div>
                  )}
                  {maxSessions != null && (
                    <div className='flex items-center gap-2 text-sm'>
                      <Monitor className='h-4 w-4 text-muted-foreground' />
                      <span className='text-muted-foreground'>最大会话数:</span>
                      <span>{maxSessions || '无限制'}</span>
                    </div>
                  )}
                  {remoteClientBitrateLimit != null && remoteClientBitrateLimit > 0 && (
                    <div className='flex items-center gap-2 text-sm'>
                      <Globe className='h-4 w-4 text-muted-foreground' />
                      <span className='text-muted-foreground'>远端码率限制:</span>
                      <span>{(remoteClientBitrateLimit / 1000000).toFixed(1)} Mbps</span>
                    </div>
                  )}
                </div>

                {data.ban_info?.action && (
                  <div className='rounded-lg border border-destructive/30 bg-destructive/5 p-3 space-y-1'>
                    <div className='text-sm font-medium text-destructive'>封禁信息</div>
                    <div className='grid gap-1 text-xs text-muted-foreground'>
                      {data.ban_info.timestamp && <div>封禁时间: {data.ban_info.timestamp}</div>}
                      {data.ban_info.trigger_ip && <div>触发IP: {data.ban_info.trigger_ip}</div>}
                      {data.ban_info.active_sessions != null && <div>触发时会话数: {data.ban_info.active_sessions}</div>}
                      <div>处理方式: {data.ban_info.action}</div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {data.active_sessions?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>正在播放</CardTitle>
                  <CardDescription>{data.active_sessions.length} 个活跃会话</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='grid gap-2'>
                    {data.active_sessions.map((session, i) => (
                      <div key={i} className='rounded-lg border p-3'>
                        <div className='font-medium'>{session.media_name || '未知内容'}</div>
                        <div className='text-xs text-muted-foreground'>{session.client_type || '-'} · {session.device_name || '-'}</div>
                        {session.ip_address && <div className='text-xs text-muted-foreground'>IP: {session.ip_address}</div>}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle>播放记录</CardTitle>
                <CardDescription>{data.playback_records?.length || 0} 条记录</CardDescription>
              </CardHeader>
              <CardContent>
                {data.playback_records?.length > 0 ? (
                  <div className='hidden md:block overflow-x-auto'>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className='w-[35%]'>内容</TableHead>
                          <TableHead className='w-[12%]'>设备</TableHead>
                          <TableHead className='w-[12%]'>IP</TableHead>
                          <TableHead className='w-[15%]'>位置</TableHead>
                          <TableHead className='w-[10%]'>时长</TableHead>
                          <TableHead className='w-[16%]'>时间</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {data.playback_records.map((record, i) => (
                          <TableRow key={i}>
                            <TableCell className='font-medium'>
                              <div className='flex items-center gap-2'>
                                <Play className='size-4 text-muted-foreground' />
                                <span className='truncate'>{record.media_name || '未知内容'}</span>
                              </div>
                            </TableCell>
                            <TableCell className='whitespace-nowrap'>{record.device_name || '-'}</TableCell>
                            <TableCell className='whitespace-nowrap text-sm'>{record.ip_address || '-'}</TableCell>
                            <TableCell className='whitespace-nowrap text-sm text-muted-foreground'>{record.location || '-'}</TableCell>
                            <TableCell className='whitespace-nowrap'>{formatDuration(record.duration)}</TableCell>
                            <TableCell className='whitespace-nowrap text-sm text-muted-foreground'>
                              {record.start_time || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className='text-muted-foreground text-center py-8'>暂无播放记录</div>
                )}
              </CardContent>
            </Card>
          </div>
        ) : null}
      </Main>
    </>
  )
}
