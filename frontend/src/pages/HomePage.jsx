import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Shield } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiRequest } from '@/types/api'

export default function HomePage() {
  const [username, setUsername] = useState('')
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await apiRequest('/public/active-sessions')
        setSessions(data.sessions || [])
      } catch (e) {
        setSessions([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const onSearch = (e) => {
    e.preventDefault()
    if (!username) return
    navigate(`/search?username=${encodeURIComponent(username)}`)
  }

  return (
    <div className='mx-auto max-w-6xl space-y-6 p-4 md:p-8'>
      <div className='flex items-center justify-between'>
        <h1 className='text-2xl font-bold'>Emby 播放记录查询</h1>
        <Button variant='outline' onClick={() => navigate('/login')}>
          <Shield className='mr-2 h-4 w-4' /> 管理员登录
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>按用户名查询</CardTitle>
        </CardHeader>
        <CardContent>
          <form className='flex gap-2' onSubmit={onSearch}>
            <Input
              placeholder='输入 Emby 用户名'
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <Button type='submit'>
              <Search className='mr-2 h-4 w-4' /> 查询
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>当前正在播放（{sessions.length}）</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className='text-sm text-muted-foreground'>加载中...</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>用户</TableHead>
                  <TableHead>IP</TableHead>
                  <TableHead>位置</TableHead>
                  <TableHead>设备</TableHead>
                  <TableHead>客户端</TableHead>
                  <TableHead>内容</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.map((s) => (
                  <TableRow key={s.session_id}>
                    <TableCell>{s.username}</TableCell>
                    <TableCell>{s.ip_address}</TableCell>
                    <TableCell>{s.location}</TableCell>
                    <TableCell>{s.device}</TableCell>
                    <TableCell>{s.client}</TableCell>
                    <TableCell>{s.media}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
