import { useCallback, useEffect, useState } from 'react'
import { Film, LoaderCircle, MessageSquare, Tv } from 'lucide-react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { apiRequest } from '@/types/api'
import { formatTime, WISH_STATUS_LABELS } from '@/types/format'
import { CommentSection } from '@/pages/UserRequestsPage'

const STATUS_ACTIONS = [
  { value: 'pending', label: '待处理' },
  { value: 'approved', label: '已采纳' },
  { value: 'rejected', label: '已拒绝' },
]

function AdminCommentDialog({ item, open, onOpenChange }) {
  const titleText = item?.title || item?.original_title || '未命名内容'
  const itemStatus = item?.request_status || item?.status || 'pending'

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='flex max-h-[85vh] flex-col gap-0 p-0 sm:max-w-lg'>
        <DialogHeader className='shrink-0 border-b px-6 py-4'>
          <DialogTitle className='text-base'>{titleText}</DialogTitle>
          <DialogDescription className='flex items-center gap-2 text-xs'>
            <span>{item?.year || item?.release_date || '未知年份'}</span>
            <Badge variant='outline' className='h-5 px-1.5 text-[10px]'>
              {item?.media_type === 'movie' ? (
                <span className='inline-flex items-center gap-1'><Film className='h-3 w-3' /> 电影</span>
              ) : (
                <span className='inline-flex items-center gap-1'><Tv className='h-3 w-3' /> 剧集</span>
              )}
            </Badge>
            <Badge variant={itemStatus === 'rejected' ? 'destructive' : itemStatus === 'approved' ? 'default' : 'outline'} className='h-5 px-1.5 text-[10px]'>
              {WISH_STATUS_LABELS[itemStatus] || '待处理'}
            </Badge>
          </DialogDescription>
        </DialogHeader>
        {item && <CommentSection requestId={item.id} apiPrefix='admin' />}
      </DialogContent>
    </Dialog>
  )
}

export default function AdminWishesPage() {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [commentItem, setCommentItem] = useState(null)

  const loadRequests = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest('/admin/wishes')
      setRequests(data.requests || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRequests()
  }, [loadRequests])

  const updateStatus = async (requestId, status) => {
    try {
      await apiRequest(`/admin/wishes/${requestId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      })
      setNotice(`状态已更新为${WISH_STATUS_LABELS[status] || status}`)
      await loadRequests()
    } catch (err) {
      setError(err.message)
    }
  }

  const deleteRequest = async (requestId) => {
    if (!window.confirm('确定删除此求片记录？')) return
    try {
      await apiRequest(`/admin/wishes/${requestId}`, { method: 'DELETE' })
      setNotice('已删除')
      await loadRequests()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <Header>
        <h1 className='text-lg font-medium'>求片管理</h1>
      </Header>
      <Main>
        {error && <p className='mb-4 text-sm text-destructive'>{error}</p>}
        {notice && <p className='mb-4 text-sm text-primary'>{notice}</p>}

        {loading ? (
          <div className='flex items-center justify-center py-12'>
            <LoaderCircle className='h-6 w-6 animate-spin text-muted-foreground' />
          </div>
        ) : requests.length === 0 ? (
          <Card>
            <CardContent className='py-8 text-center text-sm text-muted-foreground'>
              暂无求片记录
            </CardContent>
          </Card>
        ) : (
          <div className='grid gap-4'>
            {requests.map((item) => {
              const titleText = item.title || item.original_title || '未命名内容'
              const itemStatus = item.request_status || item.status || 'pending'
              return (
                <Card key={item.id}>
                  <CardContent className='p-4'>
                    <div className='flex items-start gap-4'>
                      {item.poster_url ? (
                        <img src={item.poster_url} alt={titleText} className='h-24 w-16 rounded object-cover shrink-0' />
                      ) : (
                        <div className='flex h-24 w-16 items-center justify-center rounded bg-muted text-xs text-muted-foreground shrink-0'>
                          无图
                        </div>
                      )}
                      <div className='flex-1 min-w-0'>
                        <div className='flex items-center gap-2'>
                          <span className='font-medium truncate'>{titleText}</span>
                          <Badge variant='outline' className='shrink-0 text-[10px]'>
                            {item.media_type === 'movie' ? '电影' : '剧集'}
                          </Badge>
                          <Badge variant={itemStatus === 'rejected' ? 'destructive' : itemStatus === 'approved' ? 'default' : 'outline'} className='shrink-0 text-[10px]'>
                            {WISH_STATUS_LABELS[itemStatus] || '待处理'}
                          </Badge>
                        </div>
                        <div className='mt-1 text-xs text-muted-foreground'>
                          {item.year || item.release_date || ''} · 提交于 {formatTime(item.created_at)}
                        </div>
                        {item.overview && (
                          <p className='mt-1 text-xs text-muted-foreground line-clamp-2'>{item.overview}</p>
                        )}
                        <div className='mt-3 flex flex-wrap items-center gap-2'>
                          {STATUS_ACTIONS.map((action) => (
                            <Button
                              key={action.value}
                              size='sm'
                              variant={itemStatus === action.value ? 'default' : 'outline'}
                              onClick={() => updateStatus(item.id, action.value)}
                              disabled={itemStatus === action.value}
                            >
                              {action.label}
                            </Button>
                          ))}
                          <Button size='sm' variant='ghost' onClick={() => setCommentItem(item)}>
                            <MessageSquare className='mr-1 h-3 w-3' />
                            评论
                          </Button>
                          <Button size='sm' variant='destructive' onClick={() => deleteRequest(item.id)}>
                            删除
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}

        <AdminCommentDialog item={commentItem} open={!!commentItem} onOpenChange={(open) => { if (!open) setCommentItem(null) }} />
      </Main>
    </>
  )
}
