import { useEffect, useState } from 'react'
import { apiRequest } from '@/types/api'
import { formatDuration } from '@/types/format'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

export default function UserPlaybackPage() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiRequest('/user/playback-history?limit=50')
      .then((data) => setRecords(data.records || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <Header>
        <h1 className='text-lg font-medium'>播放记录</h1>
      </Header>
      <Main>
        <Card>
          <CardHeader>
            <CardTitle>播放记录</CardTitle>
            <CardDescription>你最近的播放历史</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className='text-muted-foreground'>加载中...</div>
            ) : records.length === 0 ? (
              <div className='text-muted-foreground'>暂无播放记录</div>
            ) : (
              <>
                <div className='hidden md:block'>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>IP</TableHead>
                        <TableHead>位置</TableHead>
                        <TableHead>设备</TableHead>
                        <TableHead>客户端</TableHead>
                        <TableHead>内容</TableHead>
                        <TableHead>开始时间</TableHead>
                        <TableHead>时长</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {records.map((r, i) => (
                        <TableRow key={i}>
                          <TableCell className='font-mono text-xs'>{r.ip_address}</TableCell>
                          <TableCell>{r.location || '-'}</TableCell>
                          <TableCell>{r.device_name || '-'}</TableCell>
                          <TableCell>{r.client_type || '-'}</TableCell>
                          <TableCell className='max-w-[200px] truncate'>{r.media_name || '-'}</TableCell>
                          <TableCell className='text-xs'>{r.start_time ? new Date(r.start_time).toLocaleString('zh-CN') : '-'}</TableCell>
                          <TableCell>{formatDuration(r.duration)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <div className='grid gap-3 md:hidden'>
                  {records.map((r, i) => (
                    <div key={i} className='rounded-lg border p-3 space-y-1'>
                      <div className='font-medium truncate'>{r.media_name || '-'}</div>
                      <div className='text-xs text-muted-foreground'>{r.ip_address} · {r.location || '-'}</div>
                      <div className='text-xs text-muted-foreground'>{r.device_name || '-'} · {r.client_type || '-'}</div>
                      <div className='text-xs text-muted-foreground'>{r.start_time ? new Date(r.start_time).toLocaleString('zh-CN') : '-'} · {formatDuration(r.duration)}</div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
