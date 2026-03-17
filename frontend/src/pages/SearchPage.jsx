import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiRequest } from '@/types/api'

export default function SearchPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const params = new URLSearchParams(location.search)
  const username = params.get('username') || ''
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!username) return
    const load = async () => {
      try {
        const res = await apiRequest(`/public/search?username=${encodeURIComponent(username)}`)
        setData(res)
      } catch (err) {
        setError(err.message)
      }
    }
    load()
  }, [username])

  if (!username) {
    return <div className='p-8 text-center text-muted-foreground'>缺少用户名参数</div>
  }

  if (error) {
    return <div className='p-8 text-center text-destructive'>{error}</div>
  }

  if (!data) {
    return <div className='p-8 text-center text-muted-foreground'>加载中...</div>
  }

  const { user_info, playback_records, ban_info, active_sessions } = data

  return (
    <div className='mx-auto max-w-6xl space-y-6 p-4 md:p-8'>
      <div className='flex items-center justify-between'>
        <h1 className='text-2xl font-bold'>用户详情：{username}</h1>
        <Button variant='outline' onClick={() => navigate('/')}>
          返回首页
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>用户状态</CardTitle>
        </CardHeader>
        <CardContent className='flex items-center gap-4'>
          <div className='text-sm text-muted-foreground'>用户ID: {user_info?.Id || '-'}</div>
          <Badge variant={user_info?.Policy?.IsDisabled ? 'destructive' : 'default'}>
            {user_info?.Policy?.IsDisabled ? '已禁用' : '正常'}
          </Badge>
        </CardContent>
      </Card>

      {active_sessions?.length ? (
        <Card>
          <CardHeader>
            <CardTitle>正在播放</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>IP</TableHead>
                  <TableHead>位置</TableHead>
                  <TableHead>设备</TableHead>
                  <TableHead>客户端</TableHead>
                  <TableHead>内容</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {active_sessions.map((s) => (
                  <TableRow key={s.session_id}>
                    <TableCell>{s.ip_address}</TableCell>
                    <TableCell>{s.location}</TableCell>
                    <TableCell>{s.device}</TableCell>
                    <TableCell>{s.client}</TableCell>
                    <TableCell>{s.media}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}

      {ban_info ? (
        <Card>
          <CardHeader>
            <CardTitle>封禁信息</CardTitle>
          </CardHeader>
          <CardContent className='space-y-1 text-sm'>
            <p>时间：{ban_info.timestamp}</p>
            <p>触发IP：{ban_info.trigger_ip}</p>
            <p>并发会话：{ban_info.active_sessions}</p>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>最近播放记录</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>IP</TableHead>
                <TableHead>位置</TableHead>
                <TableHead>设备</TableHead>
                <TableHead>客户端</TableHead>
                <TableHead>内容</TableHead>
                <TableHead>开始</TableHead>
                <TableHead>结束</TableHead>
                <TableHead>时长</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {playback_records?.map((r) => (
                <TableRow key={`${r.session_id}-${r.start_time}`}>
                  <TableCell>{r.ip_address}</TableCell>
                  <TableCell>{r.location}</TableCell>
                  <TableCell>{r.device_name}</TableCell>
                  <TableCell>{r.client_type}</TableCell>
                  <TableCell>{r.media_name}</TableCell>
                  <TableCell>{r.start_time}</TableCell>
                  <TableCell>{r.end_time || '播放中'}</TableCell>
                  <TableCell>{r.duration ?? '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
