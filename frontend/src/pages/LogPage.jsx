import { useEffect, useState, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiRequest } from '@/types/api'

export default function LogPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const logContainerRef = useRef(null)

  useEffect(() => {
    const loadLogs = async () => {
      try {
        const response = await apiRequest('/admin/logs')
        setLogs(response.logs || [])
      } catch (e) {
        console.error('加载日志失败:', e)
      } finally {
        setLoading(false)
      }
    }
    loadLogs()
  }, [])

  useEffect(() => {
    // 滚动到最新的日志
    if (!loading && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs, loading])

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl p-4 pb-8 md:p-8">
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">加载中...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl p-4 pb-8 md:p-8">
      <Card>
        <CardHeader>
          <CardTitle>运行日志</CardTitle>
        </CardHeader>
        <CardContent>
          <div 
            ref={logContainerRef}
            className="max-h-[600px] overflow-y-auto border rounded-md p-4 bg-muted/50 font-mono text-sm"
          >
            {logs.length === 0 ? (
              <p className="text-muted-foreground text-center">暂无日志</p>
            ) : (
              <div className="space-y-1">
                {logs.map((log, index) => (
                  <div key={index} className="whitespace-pre-wrap break-all">
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}