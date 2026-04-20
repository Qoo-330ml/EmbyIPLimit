import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronDown, Film, LoaderCircle, MessageSquare, Reply, Send, Trash2, Tv, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { RequestModal } from '@/pages/HomePage'
import { apiRequest } from '@/types/api'
import { formatTime, WISH_STATUS_LABELS } from '@/types/format'

function StatusOverlay({ status, inLibrary }) {
  if (status === 'rejected') {
    return (
      <div className='absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/45 text-white'>
        <div className='flex h-10 w-10 items-center justify-center rounded-full bg-red-500/90 shadow-lg'>✕</div>
        <span className='rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium'>已拒绝</span>
      </div>
    )
  }
  if (status === 'approved') {
    return (
      <div className='absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/45 text-white'>
        <div className='flex h-10 w-10 items-center justify-center rounded-full bg-teal-500/90 shadow-lg'>✓</div>
        <span className='rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium'>已采纳</span>
      </div>
    )
  }
  if (inLibrary) {
    return (
      <div className='absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/45 text-white'>
        <div className='flex h-10 w-10 items-center justify-center rounded-full bg-green-500/90 shadow-lg'>✓</div>
        <span className='rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium'>已入库</span>
      </div>
    )
  }
  if (status === 'pending') {
    return (
      <div className='absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/45 text-white'>
        <div className='flex h-10 w-10 items-center justify-center rounded-full bg-yellow-500/90 shadow-lg'>
          <LoaderCircle className='h-5 w-5 animate-spin' />
        </div>
        <span className='rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium'>待处理</span>
      </div>
    )
  }
  return null
}

function CommentSection({ requestId, apiPrefix }) {
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(false)
  const [newContent, setNewContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [replyTo, setReplyTo] = useState(null)
  const listRef = useRef(null)
  const inputRef = useRef(null)

  const loadComments = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiRequest(`/${apiPrefix}/wishes/${requestId}/comments?page=1&page_size=100`)
      setComments(data.comments || [])
    } catch {
    } finally {
      setLoading(false)
    }
  }, [requestId, apiPrefix])

  useEffect(() => {
    loadComments()
  }, [loadComments])

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [comments])

  const handleSubmit = async () => {
    const content = newContent.trim()
    if (!content || submitting) return
    setSubmitting(true)
    try {
      const body = { content }
      if (replyTo) {
        body.reply_to_id = replyTo.id
      }
      const data = await apiRequest(`/${apiPrefix}/wishes/${requestId}/comments`, {
        method: 'POST',
        body: JSON.stringify(body),
      })
      if (data.comment) {
        setComments((prev) => [...prev, data.comment])
        setNewContent('')
        setReplyTo(null)
      }
    } catch {
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (commentId) => {
    try {
      await apiRequest(`/${apiPrefix}/wishes/comments/${commentId}`, { method: 'DELETE' })
      setComments((prev) => prev.filter((c) => c.id !== commentId))
    } catch {
    }
  }

  const handleReply = (comment) => {
    setReplyTo(comment)
    setNewContent(`@${comment.username} `)
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }

  const cancelReply = () => {
    setReplyTo(null)
    setNewContent('')
  }

  const buildCommentTree = (flatComments) => {
    const map = {}
    const roots = []
    flatComments.forEach((c) => {
      map[c.id] = { ...c, children: [] }
    })
    flatComments.forEach((c) => {
      if (c.reply_to_id && map[c.reply_to_id]) {
        map[c.reply_to_id].children.push(map[c.id])
      } else {
        roots.push(map[c.id])
      }
    })
    return roots
  }

  const commentTree = buildCommentTree(comments)

  const renderComment = (c, depth = 0) => (
    <div key={c.id} className={depth > 0 ? 'ml-4 border-l pl-3' : ''}>
      <div className='group flex gap-2 py-1.5 cursor-pointer rounded px-1 -mx-1 hover:bg-muted/50' onClick={() => handleReply(c)}>
        <span className='shrink-0 text-xs font-medium text-primary/80'>{c.username}</span>
        <div className='min-w-0 flex-1'>
          <p className='break-words text-xs leading-4'>{c.content}</p>
          <div className='flex items-center gap-2'>
            <span className='text-[10px] text-muted-foreground'>{formatTime(c.created_at)}</span>
            <span className='text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-0.5'>
              <Reply className='h-2.5 w-2.5' />
              回复
            </span>
          </div>
        </div>
        <button
          className='shrink-0 self-start rounded p-0.5 hover:bg-muted'
          onClick={(e) => { e.stopPropagation(); handleDelete(c.id); }}
          title='删除评论'
        >
          <Trash2 className='h-3 w-3 text-muted-foreground hover:text-destructive' />
        </button>
      </div>
      {c.children && c.children.length > 0 && (
        <div className='space-y-0'>
          {c.children.map((child) => renderComment(child, depth + 1))}
        </div>
      )}
    </div>
  )

  return (
    <div className='flex flex-1 flex-col'>
      <div ref={listRef} className='max-h-80 flex-1 overflow-y-auto px-4 py-3'>
        {loading && comments.length === 0 && (
          <p className='py-4 text-center text-xs text-muted-foreground'>加载评论中...</p>
        )}
        {!loading && comments.length === 0 && (
          <p className='py-4 text-center text-xs text-muted-foreground'>暂无评论，来说点什么吧</p>
        )}
        {commentTree.map((c) => renderComment(c))}
      </div>
      <div className='border-t px-4 py-3'>
        {replyTo && (
          <div className='mb-2 flex items-center gap-2 rounded bg-muted px-2 py-1 text-xs'>
            <Reply className='h-3 w-3' />
            <span>回复 <strong>{replyTo.username}</strong></span>
            <button className='ml-auto' onClick={cancelReply}>
              <X className='h-3 w-3 text-muted-foreground hover:text-foreground' />
            </button>
          </div>
        )}
        <div className='flex gap-2'>
          <Textarea
            ref={inputRef}
            className='min-h-8 resize-none py-1.5 text-xs'
            placeholder='写评论...'
            rows={1}
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit()
              }
            }}
            maxLength={500}
          />
          <Button
            className='h-8 shrink-0 self-end px-3'
            disabled={!newContent.trim() || submitting}
            size='sm'
            onClick={handleSubmit}
          >
            {submitting ? <LoaderCircle className='h-3.5 w-3.5 animate-spin' /> : <Send className='h-3.5 w-3.5' />}
          </Button>
        </div>
      </div>
    </div>
  )
}

function PosterCard({ item, onComment }) {
  const titleText = item.title || item.original_title || '未命名内容'
  const itemStatus = item.request_status || item.status || 'pending'

  return (
    <div className='flex flex-col overflow-hidden rounded-lg border bg-card transition-shadow hover:shadow-md'>
      <div className='relative aspect-[3/4] w-full shrink-0 overflow-hidden bg-muted'>
        {item.poster_url ? (
          <img src={item.poster_url} alt={titleText} className='absolute inset-0 h-full w-full object-cover' />
        ) : (
          <div className='flex h-full items-center justify-center px-3 text-center text-xs text-muted-foreground'>暂无海报</div>
        )}
        <StatusOverlay status={itemStatus} inLibrary={item.in_library} />
        <div className='absolute left-2.5 top-2.5'>
          <Badge className='bg-primary text-primary-foreground border-0 px-2 py-0.5 text-[11px] font-medium'>
            {item.media_type === 'movie' ? '电影' : '剧集'}
          </Badge>
        </div>
        <div className='absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-2.5 pt-8'>
          <div className='text-[11px] text-white/70'>{item.year || item.release_date || ''}</div>
          <div className='line-clamp-1 text-sm font-medium leading-tight text-white'>{titleText}</div>
          <div className='line-clamp-1 text-[11px] leading-tight text-white/60'>{item.overview || ''}</div>
        </div>
      </div>
      <div className='flex items-center justify-between px-2.5 py-1.5'>
        <span className='text-[11px] text-muted-foreground'>{WISH_STATUS_LABELS[itemStatus] || '待处理'}</span>
        <button
          className='inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] transition-colors hover:bg-muted hover:text-foreground'
          onClick={onComment}
        >
          <MessageSquare className='h-3 w-3' />
          评论
        </button>
      </div>
    </div>
  )
}

function CommentDialog({ item, open, onOpenChange, apiPrefix }) {
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
        {item && <CommentSection requestId={item.id} apiPrefix={apiPrefix} />}
      </DialogContent>
    </Dialog>
  )
}

function WishGrid({ items, onComment }) {
  return (
    <div className='grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5'>
      {items.map((item) => {
        const itemKey = `${item.media_type}-${item.tmdb_id}-${item.id || 'wish'}`
        return <PosterCard key={itemKey} item={item} onComment={() => onComment(item)} />
      })}
    </div>
  )
}

export { CommentSection }

export default function UserRequestsPage() {
  const navigate = useNavigate()
  const [showModal, setShowModal] = useState(false)
  const [userWishes, setUserWishes] = useState([])
  const [loadingWishes, setLoadingWishes] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalResults, setTotalResults] = useState(0)
  const [commentItem, setCommentItem] = useState(null)

  const [allWishes, setAllWishes] = useState([])
  const [loadingAll, setLoadingAll] = useState(false)
  const [loadingAllMore, setLoadingAllMore] = useState(false)
  const [allPage, setAllPage] = useState(1)
  const [allTotalPages, setAllTotalPages] = useState(1)
  const [allTotalResults, setAllTotalResults] = useState(0)

  const loadWishes = useCallback(async (pageNum = 1, append = false) => {
    if (append) {
      setLoadingMore(true)
    } else {
      setLoadingWishes(true)
    }
    setError('')
    try {
      const data = await apiRequest(`/user/wishes?page=${pageNum}&page_size=25`)
      setUserWishes((prev) => (append ? [...prev, ...(data.requests || [])] : (data.requests || [])))
      setPage(data.page || 1)
      setTotalPages(data.total_pages || 1)
      setTotalResults(data.total_results || (data.requests || []).length)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingWishes(false)
      setLoadingMore(false)
    }
  }, [navigate])

  const loadAllWishes = useCallback(async (pageNum = 1, append = false) => {
    if (append) {
      setLoadingAllMore(true)
    } else {
      setLoadingAll(true)
    }
    try {
      const data = await apiRequest(`/user/wishes/all?page=${pageNum}&page_size=25`)
      setAllWishes((prev) => (append ? [...prev, ...(data.requests || [])] : (data.requests || [])))
      setAllPage(data.page || 1)
      setAllTotalPages(data.total_pages || 1)
      setAllTotalResults(data.total_results || (data.requests || []).length)
    } catch {
    } finally {
      setLoadingAll(false)
      setLoadingAllMore(false)
    }
  }, [])

  useEffect(() => {
    loadWishes(1)
  }, [loadWishes])

  useEffect(() => {
    loadAllWishes(1)
  }, [loadAllWishes])

  const handleLoadMore = () => {
    if (page < totalPages) {
      loadWishes(page + 1, true)
    }
  }

  const handleAllLoadMore = () => {
    if (allPage < allTotalPages) {
      loadAllWishes(allPage + 1, true)
    }
  }

  const handleComment = (item) => {
    setCommentItem(item)
  }

  return (
    <>
      <Header>
        <h1 className='text-lg font-medium'>媒体请求</h1>
      </Header>
      <Main>
        <div className='mb-6'>
          <h2 className='mb-2 text-lg font-semibold'>求片</h2>
          <p className='mb-3 text-sm text-muted-foreground'>搜索并提交你想看的影视内容</p>
          <Button onClick={() => setShowModal(true)}>开始求片</Button>
        </div>

        <Card className='mb-6'>
          <CardHeader>
            <CardTitle>我的求片</CardTitle>
            <CardDescription>你提交的求片记录，点击评论查看详情</CardDescription>
            {totalResults > 0 && (
              <p className='mt-1 text-xs text-muted-foreground'>共 {totalResults} 条</p>
            )}
          </CardHeader>
          <CardContent>
            {error && <p className='mb-4 text-sm text-destructive'>{error}</p>}
            {loadingWishes && <p className='text-sm text-muted-foreground'>加载求片列表中...</p>}

            {!loadingWishes && userWishes.length > 0 && (
              <>
                <WishGrid
                  items={userWishes}
                  onComment={handleComment}
                />

                {page < totalPages && (
                  <div className='mt-4 flex justify-center'>
                    <Button variant='outline' onClick={handleLoadMore} disabled={loadingMore}>
                      {loadingMore ? <LoaderCircle className='mr-2 h-4 w-4 animate-spin' /> : <ChevronDown className='mr-2 h-4 w-4' />}
                      {loadingMore ? '加载中...' : '加载更多'}
                    </Button>
                  </div>
                )}
              </>
            )}

            {!loadingWishes && !userWishes.length && !error && (
              <p className='py-8 text-center text-sm text-muted-foreground'>你还没有提交过求片内容</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>所有求片</CardTitle>
            <CardDescription>所有用户提交的求片记录</CardDescription>
            {allTotalResults > 0 && (
              <p className='mt-1 text-xs text-muted-foreground'>共 {allTotalResults} 条</p>
            )}
          </CardHeader>
          <CardContent>
            {loadingAll && <p className='text-sm text-muted-foreground'>加载中...</p>}

            {!loadingAll && allWishes.length > 0 && (
              <>
                <WishGrid
                  items={allWishes}
                  onComment={handleComment}
                />

                {allPage < allTotalPages && (
                  <div className='mt-4 flex justify-center'>
                    <Button variant='outline' onClick={handleAllLoadMore} disabled={loadingAllMore}>
                      {loadingAllMore ? <LoaderCircle className='mr-2 h-4 w-4 animate-spin' /> : <ChevronDown className='mr-2 h-4 w-4' />}
                      {loadingAllMore ? '加载中...' : '加载更多'}
                    </Button>
                  </div>
                )}
              </>
            )}

            {!loadingAll && !allWishes.length && (
              <p className='py-8 text-center text-sm text-muted-foreground'>暂无求片记录</p>
            )}
          </CardContent>
        </Card>

        <CommentDialog item={commentItem} open={!!commentItem} onOpenChange={(open) => { if (!open) setCommentItem(null) }} apiPrefix='user' />
        <RequestModal open={showModal} onClose={() => setShowModal(false)} onSuccess={() => { loadWishes(1); loadAllWishes(1); }} />
      </Main>
    </>
  )
}
