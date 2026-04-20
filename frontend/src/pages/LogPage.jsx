import { useEffect, useState, useRef, useMemo } from 'react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiRequest } from '@/types/api'
import { Play, Square, Trash2, Download } from 'lucide-react'

export default function LogPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterText, setFilterText] = useState('')
  const [autoScroll, setAutoScroll] = useState(true)
  const scrollRef = useRef(null)
  const pollingRef = useRef(null)

  const parseLogs = (logText) => {
    const lines = logText.split('\n').filter(line => line.trim())
    return lines.map((line, index) => {
      const timestampMatch = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/)
      const timestamp = timestampMatch ? timestampMatch[1] : null
      const content = timestampMatch ? line.slice(timestamp.length + 1).trim() : line
      
      let type
      if (line.includes('[▶]') || line.includes('[■]')) {
        type = 'playback'
      } else if (line.includes('[SYS]')) {
        type = 'system'
      } else if (line.includes('[API]')) {
        type = 'activity'
      } else {
        type = 'system'
      }

      return {
        id: index,
        timestamp,
        content,
        type,
        original: line
      }
    })
  }

  const fetchLogs = () => {
    apiRequest('/admin/logs')
      .then((data) => {
        let logText = ''
        if (typeof data === 'string') {
          logText = data
        } else if (Array.isArray(data)) {
          logText = data.join('\n')
        } else if (data && typeof data === 'object') {
          const logsArray = data.logs || data.log || data.content
          if (Array.isArray(logsArray)) {
            logText = logsArray.join('\n')
          } else if (typeof logsArray === 'string') {
            logText = logsArray
          } else {
            logText = JSON.stringify(data, null, 2)
          }
        } else {
          logText = String(data || '')
        }
        const parsedLogs = parseLogs(logText)
        setLogs(parsedLogs)
      })
      .catch((error) => {
        console.error('日志加载失败:', error)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchLogs()
    pollingRef.current = setInterval(fetchLogs, 3000)

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      const viewport = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight
      }
    }
  }, [logs, autoScroll])

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return ''
    const [, time] = timestamp.split(' ')
    return time
  }

  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      const matchesFilter = log.original.toLowerCase().includes(filterText.toLowerCase())
      return matchesFilter
    })
  }, [logs, filterText])

  const logsByType = useMemo(() => {
    return {
      all: filteredLogs,
      activity: filteredLogs.filter(log => log.type === 'activity'),
      playback: filteredLogs.filter(log => log.type === 'playback'),
      system: filteredLogs.filter(log => log.type === 'system')
    }
  }, [filteredLogs])

  const getLogColor = (type) => {
    switch (type) {
      case 'playback': return 'text-green-600 dark:text-green-400'
      case 'activity': return 'text-blue-600 dark:text-blue-400'
      case 'system': return 'text-purple-600 dark:text-purple-400'
      default: return 'text-foreground'
    }
  }

  const getBadgeVariant = (type) => {
    switch (type) {
      case 'playback': return 'default'
      case 'activity': return 'outline'
      case 'system': return 'secondary'
      default: return 'secondary'
    }
  }

  const handleClearLogs = () => {
    setLogs([])
  }

  const handleExportLogs = () => {
    const logContent = logs.map(log => log.original).join('\n')
    const blob = new Blob([logContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const LogEntry = ({ log }) => (
    <div className='flex gap-2 py-1 border-b border-muted last:border-0 hover:bg-muted/30 px-2 rounded'>
      <span className='text-xs text-muted-foreground font-mono min-w-[80px]'>
        {formatTimestamp(log.timestamp)}
      </span>
      <Badge variant={getBadgeVariant(log.type)} className='h-5 text-xs shrink-0'>
        {log.type.toUpperCase()}
      </Badge>
      <span className={`text-sm font-mono flex-1 break-all ${getLogColor(log.type)}`}>
        {log.content}
      </span>
    </div>
  )

  return (
    <>
      <Header>
        <div className='flex items-center justify-between w-full'>
          <h1 className='text-lg font-medium'>日志</h1>
          <div className='flex items-center gap-2'>
            <Button
              variant={autoScroll ? 'default' : 'outline'}
              size='sm'
              onClick={() => setAutoScroll(!autoScroll)}
              className='h-8'
            >
              {autoScroll ? <Square className='size-4 mr-1' /> : <Play className='size-4 mr-1' />}
              自动滚动
            </Button>
            <Button variant='outline' size='sm' onClick={handleClearLogs} className='h-8'>
              <Trash2 className='size-4 mr-1' />
              清空
            </Button>
            <Button variant='outline' size='sm' onClick={handleExportLogs} className='h-8'>
              <Download className='size-4 mr-1' />
              导出
            </Button>
          </div>
        </div>
      </Header>
      <Main>
        <Card>
          <CardHeader>
            <div className='flex items-center justify-between gap-4'>
              <div>
                <CardTitle>系统日志</CardTitle>
                <CardDescription>查看服务器运行日志</CardDescription>
              </div>
              <Input
                placeholder='搜索日志...'
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                className='max-w-[300px]'
              />
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className='text-muted-foreground'>加载中...</div>
            ) : (
              <Tabs defaultValue='all' className='w-full'>
                <TabsList className='grid w-full grid-cols-4 mb-4'>
                <TabsTrigger value='all'>全部 ({logsByType.all.length})</TabsTrigger>
                <TabsTrigger value='activity'>活动 ({logsByType.activity.length})</TabsTrigger>
                <TabsTrigger value='playback'>播放 ({logsByType.playback.length})</TabsTrigger>
                <TabsTrigger value='system'>系统 ({logsByType.system.length})</TabsTrigger>
              </TabsList>
                
                <TabsContent value='all' className='mt-0'>
                  <ScrollArea ref={scrollRef} className='h-[600px] w-full rounded-md border bg-muted/30 p-2'>
                    {filteredLogs.length === 0 ? (
                      <div className='text-muted-foreground text-center py-8'>暂无日志</div>
                    ) : (
                      filteredLogs.map(log => <LogEntry key={log.id} log={log} />)
                    )}
                  </ScrollArea>
                </TabsContent>
                
                <TabsContent value='activity' className='mt-0'>
                  <ScrollArea ref={scrollRef} className='h-[600px] w-full rounded-md border bg-muted/30 p-2'>
                    {logsByType.activity.length === 0 ? (
                      <div className='text-muted-foreground text-center py-8'>暂无活动日志</div>
                    ) : (
                      logsByType.activity.map(log => <LogEntry key={log.id} log={log} />)
                    )}
                  </ScrollArea>
                </TabsContent>
                
                <TabsContent value='playback' className='mt-0'>
                  <ScrollArea ref={scrollRef} className='h-[600px] w-full rounded-md border bg-muted/30 p-2'>
                    {logsByType.playback.length === 0 ? (
                      <div className='text-muted-foreground text-center py-8'>暂无播放日志</div>
                    ) : (
                      logsByType.playback.map(log => <LogEntry key={log.id} log={log} />)
                    )}
                  </ScrollArea>
                </TabsContent>
                
                <TabsContent value='system' className='mt-0'>
                  <ScrollArea ref={scrollRef} className='h-[600px] w-full rounded-md border bg-muted/30 p-2'>
                    {logsByType.system.length === 0 ? (
                      <div className='text-muted-foreground text-center py-8'>暂无系统日志</div>
                    ) : (
                      logsByType.system.map(log => <LogEntry key={log.id} log={log} />)
                    )}
                  </ScrollArea>
                </TabsContent>
              </Tabs>
            )}
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
