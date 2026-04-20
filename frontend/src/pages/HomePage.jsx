import { useEffect, useState } from 'react'
import { Angry, ChevronDown, CircleCheckBig, Heart, Loader, LoaderCircle, Play, Search, Tv, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import UserIdentity from '@/components/UserIdentity'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { apiRequest } from '@/types/api'
import { WISH_STATUS_LABELS } from '@/types/format'
import { useActiveSessions, ActiveSessionCard } from '@/hooks/useActiveSessions'

function normalizeWishItem(item) {
  const seasonNumber = item.media_type === 'tv' ? Number(item.season_number || 0) : 0
  const lookupKey = item.lookup_key || `${item.media_type}:${item.tmdb_id}:${seasonNumber}`
  return {
    ...item,
    season_number: seasonNumber,
    lookup_key: lookupKey,
    is_season_request: item.media_type === 'tv' && seasonNumber > 0,
    requested: true,
    request_status: item.request_status || item.status || 'pending',
  }
}

function SeasonDetailModal({ open, onClose, item, loading, seasons, librarySeasonCount, onSubmitSeason, onConfirmLibrarySeason }) {
  const [submittingSeason, setSubmittingSeason] = useState(null)
  const [wishListSeasons, setWishListSeasons] = useState(new Set())

  useEffect(() => {
    const next = new Set(
      (seasons || [])
        .filter((season) => season.requested || season.request_id || season.request_status)
        .map((season) => season.season_number)
    )
    setWishListSeasons(next)
  }, [seasons, open])

  const handleSubmitSeason = async (season) => {
    setSubmittingSeason(season.season_number)
    try {
      await onSubmitSeason(season, item)
      setWishListSeasons((prev) => new Set([...prev, season.season_number]))
    } finally {
      setSubmittingSeason(null)
    }
  }

  if (!open) return null

  return (
    <div className='fixed inset-0 z-[70] flex items-center justify-center bg-black/60 p-4' onClick={onClose}>
      <Card className='flex max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden' onClick={(e) => e.stopPropagation()}>
        <CardHeader className='shrink-0 border-b pb-4'>
          <div className='flex items-start justify-between gap-4'>
            <div>
              <CardTitle>{item?.title || item?.name || '剧集详情'}</CardTitle>
              <p className='mt-1 text-sm text-muted-foreground'>
                共 {seasons?.length || 0} 季，Emby库中已有 {librarySeasonCount || 0} 季
              </p>
            </div>
            <Button size='icon' variant='ghost' onClick={onClose} title='关闭'>
              <X className='h-4 w-4' />
            </Button>
          </div>
        </CardHeader>
        <CardContent className='min-h-0 flex-1 overflow-y-auto p-6'>
          {loading ? (
            <div className='flex items-center justify-center py-8'>
              <LoaderCircle className='h-6 w-6 animate-spin text-muted-foreground' />
            </div>
          ) : (
            <div className='space-y-2'>
              {seasons?.map((season) => {
                const inWishList = wishListSeasons.has(season.season_number)
                return (
                <div
                  key={season.season_number}
                  className={`flex items-center justify-between rounded-lg border p-3 ${
                    season.in_library
                      ? 'border-green-500/30 bg-green-500/5'
                      : inWishList
                        ? 'border-yellow-500/30 bg-yellow-500/5'
                        : 'border-blue-500/30 bg-blue-500/5'
                  }`}
                >
                  <div className='flex items-center gap-3'>
                    {season.poster_url ? (
                      <img src={season.poster_url} alt={season.name} className='h-12 w-8 rounded object-cover' />
                    ) : (
                      <div className='flex h-12 w-8 items-center justify-center rounded bg-muted text-xs text-muted-foreground'>
                        无图
                      </div>
                    )}
                    <div>
                      <div className='font-medium'>{season.name}</div>
                      <div className='text-xs text-muted-foreground'>
                        {season.air_date ? season.air_date.slice(0, 4) : '未知年份'}
                      </div>
                    </div>
                  </div>
                  <div className='flex items-center gap-2'>
                    {season.in_library && (season.requested || inWishList) ? (
                      <Badge className='bg-yellow-500 text-black'>已在清单中</Badge>
                    ) : season.in_library ? (
                      <Button
                        size='sm'
                        className='border-2 border-green-500 bg-green-500/80 text-white hover:bg-green-600'
                        onClick={() => onConfirmLibrarySeason?.(season, item)}
                      >
                        <CircleCheckBig className='mr-1 h-4 w-4' />
                        再次求片
                      </Button>
                    ) : season.request_status === 'approved' ? (
                      <Badge className='bg-teal-500 text-white'>已采纳</Badge>
                    ) : inWishList ? (
                      <Badge className='bg-yellow-500 text-black'>已在清单中</Badge>
                    ) : (
                      <Button
                        size='sm'
                        className='border-2 border-blue-500 bg-blue-500 text-white hover:bg-blue-600'
                        onClick={() => handleSubmitSeason(season)}
                        disabled={submittingSeason === season.season_number}
                      >
                        {submittingSeason === season.season_number ? (
                          <LoaderCircle className='mr-1 h-4 w-4 animate-spin' />
                        ) : (
                          <Heart className='mr-1 h-4 w-4' />
                        )}
                        加入想看
                      </Button>
                    )}
                  </div>
                </div>
              )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function WishPosterCard({ item, submittingId, onSubmit, onShowSeasonDetail, onConfirmLibrary }) {
  const seasonNumber = item.media_type === 'tv' ? Number(item.season_number || 0) : 0
  const lookupKey = item.lookup_key || `${item.media_type}:${item.tmdb_id}:${seasonNumber}`
  const isSubmitting = submittingId === lookupKey
  const titleText = item.title || item.original_title || '未命名内容'
  const itemStatus = item.request_status || item.status
  const isRequested = Boolean(item.requested || item.request_id || item.id)
  const isApproved = itemStatus === 'approved'

  const isInLibrary = item.in_library
  const isPartiallyAvailable = item.media_type === 'tv' && isInLibrary && item.library_season_count > 0 && item.library_season_count < (item.tmdb_season_count || 0)
  const shouldSelectSeason = item.media_type === 'tv' && !item.is_season_request && !isApproved && (!isInLibrary || isPartiallyAvailable)

  const handleSubmit = () => {
    if (isSubmitting) return
    if (shouldSelectSeason) {
      if (onShowSeasonDetail) onShowSeasonDetail(item)
      return
    }
    if (isRequested || isApproved) return
    if (isInLibrary) {
      if (item.media_type === 'tv' && !item.is_season_request) {
        if (onShowSeasonDetail) onShowSeasonDetail(item)
        return
      }
      if (onConfirmLibrary) onConfirmLibrary(item)
      return
    }
    onSubmit(item)
  }

  const handleCardClick = () => {
    if (shouldSelectSeason) {
      if (onShowSeasonDetail) onShowSeasonDetail(item)
    } else if (isInLibrary && item.media_type === 'tv' && !item.is_season_request) {
      if (onShowSeasonDetail) onShowSeasonDetail(item)
    }
  }

  return (
    <div
      role='button'
      tabIndex={shouldSelectSeason ? 0 : isRequested || isApproved ? -1 : 0}
      className='flex flex-col overflow-hidden rounded-lg border bg-card text-left transition-shadow hover:shadow-md'
      onClick={handleCardClick}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          handleSubmit()
        }
      }}
    >
      <div className='relative aspect-[3/4] w-full shrink-0 overflow-hidden bg-muted'>
        {item.poster_url ? (
          <img src={item.poster_url} alt={titleText} className='absolute inset-0 h-full w-full object-cover' />
        ) : (
          <div className='flex h-full items-center justify-center px-3 text-center text-xs text-muted-foreground'>暂无海报</div>
        )}
        {isPartiallyAvailable ? (
          <div className='absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/45 text-white'>
            <div className='flex h-10 w-10 items-center justify-center rounded-full bg-red-500/90 shadow-lg'>
              <Angry className='h-5 w-5' />
            </div>
            <span className='rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium'>部分缺失</span>
          </div>
        ) : shouldSelectSeason ? (
          <div className='absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/45 text-white'>
            <div className='flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/90 shadow-lg'>
              <Tv className='h-5 w-5' />
            </div>
            <span className='rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium'>按季选择</span>
          </div>
        ) : isApproved ? (
          <div className='absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/45 text-white'>
            <div className='flex h-10 w-10 items-center justify-center rounded-full bg-teal-500/90 shadow-lg'>
              <CircleCheckBig className='h-5 w-5' />
            </div>
            <span className='rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium'>已采纳</span>
          </div>
        ) : isRequested && !isInLibrary ? (
          <div className='absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/45 text-white'>
            <div className='flex h-10 w-10 items-center justify-center rounded-full bg-yellow-500/90 shadow-lg'>
              <Loader className='h-5 w-5 animate-spin' />
            </div>
            <span className='rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium'>已在清单中</span>
          </div>
        ) : isInLibrary ? (
          <div className='absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/45 text-white'>
            <div className='flex h-10 w-10 items-center justify-center rounded-full bg-green-500/90 shadow-lg'>
              <CircleCheckBig className='h-5 w-5' />
            </div>
            <span className='rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium'>已入库</span>
          </div>
        ) : null}
        <div className='absolute left-2.5 top-2.5'>
          <Badge className='bg-primary text-primary-foreground border-0 px-2 py-0.5 text-[11px] font-medium'>
            {item.media_type === 'movie' ? '电影' : '剧集'}
          </Badge>
        </div>
        <div className='absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-2.5 pt-8'>
          <div className='text-[11px] text-white/70'>
            {item.is_season_request ? `第 ${seasonNumber} 季` : item.year || item.release_date || ''}
          </div>
          <div className='line-clamp-1 text-sm font-medium leading-tight text-white'>{titleText}</div>
          <div className='line-clamp-1 text-[11px] leading-tight text-white/60'>{item.overview || ''}</div>
        </div>
      </div>
      <div className='px-2.5 py-1.5'>
        <Button
          type='button'
          size='sm'
          variant='default'
          className={`h-10 w-full shrink-0 rounded-lg text-sm font-medium shadow-sm ${
            isPartiallyAvailable
              ? 'border-2 border-red-500 bg-red-500 text-white hover:bg-red-600'
              : shouldSelectSeason
                ? 'border-2 border-blue-500 bg-blue-500 text-white hover:bg-blue-600'
                : isApproved
                  ? 'border-2 border-teal-500 bg-teal-500 text-white hover:bg-teal-600'
                  : isRequested && !isInLibrary
                    ? 'border-2 border-yellow-500 bg-yellow-500 text-black hover:bg-yellow-600'
                    : isInLibrary
                      ? 'border-2 border-green-500 bg-green-500/80 text-white hover:bg-green-600'
                      : 'border-2 border-blue-500 bg-blue-500 text-white hover:bg-blue-600'
          }`}
          disabled={isSubmitting}
          onClick={(event) => {
            event.stopPropagation()
            handleSubmit()
          }}
        >
          {isSubmitting ? (
            <LoaderCircle className='mr-2 h-4 w-4 animate-spin' />
          ) : isPartiallyAvailable ? (
            <Angry className='mr-2 h-4 w-4' />
          ) : shouldSelectSeason ? (
            <Tv className='mr-2 h-4 w-4' />
          ) : isApproved ? (
            <CircleCheckBig className='mr-2 h-4 w-4' />
          ) : isRequested && !isInLibrary ? (
            <Loader className='mr-2 h-4 w-4 animate-spin' />
          ) : isInLibrary ? (
            <CircleCheckBig className='mr-2 h-4 w-4' />
          ) : (
            <Heart className='mr-2 h-4 w-4' />
          )}
          {isSubmitting
            ? '提交中...'
            : isPartiallyAvailable
              ? '部分缺失'
              : shouldSelectSeason
                ? '选择季'
                : isApproved
                  ? '已采纳'
                  : isRequested && !isInLibrary
                    ? '已在清单中'
                    : isInLibrary
                      ? '已入库，再次求片'
                      : '加入想看'}
        </Button>
      </div>
    </div>
  )
}

function WishListModal({
  open,
  onClose,
  items,
  loading,
  loadingMore,
  error,
  totalResults,
  page,
  totalPages,
  submittingId,
  onSubmit,
  onLoadMore,
  onShowSeasonDetail,
  onConfirmLibrary,
}) {
  if (!open) return null

  return (
    <div className='fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4' onClick={onClose}>
      <Card className='flex max-h-[88vh] w-full max-w-6xl flex-col overflow-hidden' onClick={(e) => e.stopPropagation()}>
        <CardHeader className='shrink-0 border-b pb-4'>
          <div className='flex items-start justify-between gap-4'>
            <div>
              <CardTitle>已求列表</CardTitle>
              <p className='mt-1 text-sm text-muted-foreground'>这里展示当前已经加入求片清单的影视内容。</p>
              {totalResults ? <p className='mt-1 text-xs text-muted-foreground'>共 {totalResults} 条</p> : null}
            </div>
            <Button size='icon' variant='ghost' onClick={onClose} title='关闭'>
              <X className='h-4 w-4' />
            </Button>
          </div>
        </CardHeader>
        <CardContent className='flex min-h-0 flex-1 flex-col gap-4 p-6'>
          {error ? <div className='shrink-0 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive'>{error}</div> : null}
          {loading ? <p className='shrink-0 text-sm text-muted-foreground'>正在加载已求列表...</p> : null}

          <div className='min-h-0 flex-1 overflow-y-auto pr-1'>
            <div className='grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5'>
              {items.map((item) => (
                <WishPosterCard key={`${item.media_type}-${item.tmdb_id}-${item.id || 'wish'}`} item={item} submittingId={submittingId} onSubmit={onSubmit} onShowSeasonDetail={onShowSeasonDetail} onConfirmLibrary={onConfirmLibrary} />
              ))}
            </div>

            {!loading && !items.length ? <p className='py-8 text-center text-sm text-muted-foreground'>当前还没有任何求片内容</p> : null}
          </div>

          {!loading && items.length && page < totalPages ? (
            <div className='flex shrink-0 justify-center'>
              <Button type='button' variant='outline' onClick={onLoadMore} disabled={loadingMore}>
                {loadingMore ? <LoaderCircle className='mr-2 h-4 w-4 animate-spin' /> : <ChevronDown className='mr-2 h-4 w-4' />}
                {loadingMore ? '加载中...' : '加载更多'}
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}

export function RequestModal({ open, onClose, onSuccess }) {
  const [keyword, setKeyword] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [submittingId, setSubmittingId] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalResults, setTotalResults] = useState(0)
  const [wishListOpen, setWishListOpen] = useState(false)
  const [wishList, setWishList] = useState([])
  const [loadingWishList, setLoadingWishList] = useState(false)
  const [loadingWishListMore, setLoadingWishListMore] = useState(false)
  const [wishListError, setWishListError] = useState('')
  const [wishPage, setWishPage] = useState(1)
  const [wishTotalPages, setWishTotalPages] = useState(1)
  const [wishTotalResults, setWishTotalResults] = useState(0)
  const [seasonDetailOpen, setSeasonDetailOpen] = useState(false)
  const [seasonDetailItem, setSeasonDetailItem] = useState(null)
  const [seasonDetailLoading, setSeasonDetailLoading] = useState(false)
  const [seasonDetailSeasons, setSeasonDetailSeasons] = useState([])
  const [confirmLibraryItem, setConfirmLibraryItem] = useState(null)

  useEffect(() => {
    if (!open) {
      setKeyword('')
      setResults([])
      setLoading(false)
      setLoadingMore(false)
      setSubmittingId('')
      setError('')
      setNotice('')
      setPage(1)
      setTotalPages(1)
      setTotalResults(0)
      setWishListOpen(false)
      setWishList([])
      setLoadingWishList(false)
      setLoadingWishListMore(false)
      setWishListError('')
      setWishPage(1)
      setWishTotalPages(1)
      setWishTotalResults(0)
      setSeasonDetailOpen(false)
      setSeasonDetailItem(null)
      setSeasonDetailLoading(false)
      setSeasonDetailSeasons([])
      setConfirmLibraryItem(null)
    }
  }, [open])

  useEffect(() => {
    if (!wishListOpen) {
      setWishList([])
      setLoadingWishList(false)
      setLoadingWishListMore(false)
      setWishListError('')
      setWishPage(1)
      setWishTotalPages(1)
      setWishTotalResults(0)
      return
    }

    let active = true

    const loadWishList = async () => {
      setLoadingWishList(true)
      setWishListError('')
      try {
        const data = await apiRequest('/public/wishes?page=1&page_size=20')
        if (!active) return
        setWishList((data.requests || []).map(normalizeWishItem))
        setWishPage(data.page || 1)
        setWishTotalPages(data.total_pages || 1)
        setWishTotalResults(data.total_results || (data.requests || []).length)
      } catch (err) {
        if (active) {
          setWishListError(err.message)
          setWishList([])
          setWishPage(1)
          setWishTotalPages(1)
          setWishTotalResults(0)
        }
      } finally {
        if (active) setLoadingWishList(false)
      }
    }

    loadWishList()

    return () => {
      active = false
    }
  }, [wishListOpen])

  const onSearch = async (event) => {
    event.preventDefault()
    if (!keyword.trim()) return

    setLoading(true)
    setError('')
    setNotice('')
    setResults([])
    setPage(1)
    setTotalPages(1)
    setTotalResults(0)
    try {
      const data = await apiRequest(`/public/tmdb/search?q=${encodeURIComponent(keyword.trim())}&page=1`)
      setResults(data.results || [])
      setPage(data.page || 1)
      setTotalPages(data.total_pages || 1)
      setTotalResults(data.total_results || (data.results || []).length)
      if (!(data.results || []).length) {
        setNotice('没有找到匹配的影视内容，可以换个关键词试试')
      }
    } catch (err) {
      setError(err.message)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const loadMoreSearch = async () => {
    if (loadingMore || loading || page >= totalPages || !keyword.trim()) return

    const nextPage = page + 1
    setLoadingMore(true)
    setError('')
    try {
      const data = await apiRequest(`/public/tmdb/search?q=${encodeURIComponent(keyword.trim())}&page=${nextPage}`)
      setResults((prev) => [...prev, ...(data.results || [])])
      setPage(data.page || nextPage)
      setTotalPages(data.total_pages || totalPages)
      setTotalResults(data.total_results || totalResults)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingMore(false)
    }
  }

  const loadMoreWishList = async () => {
    if (loadingWishListMore || loadingWishList || wishPage >= wishTotalPages) return

    const nextPage = wishPage + 1
    setLoadingWishListMore(true)
    setWishListError('')
    try {
      const data = await apiRequest(`/public/wishes?page=${nextPage}&page_size=20`)
      setWishList((prev) => [...prev, ...(data.requests || []).map(normalizeWishItem)])
      setWishPage(data.page || nextPage)
      setWishTotalPages(data.total_pages || wishTotalPages)
      setWishTotalResults(data.total_results || wishTotalResults)
    } catch (err) {
      setWishListError(err.message)
    } finally {
      setLoadingWishListMore(false)
    }
  }

  const showSeasonDetail = async (item) => {
    setSeasonDetailItem(item)
    setSeasonDetailOpen(true)
    setSeasonDetailLoading(true)
    setSeasonDetailSeasons([])
    try {
      const data = await apiRequest(`/public/tmdb/seasons?tmdb_id=${item.tmdb_id}`)
      setSeasonDetailSeasons(data.seasons || [])
    } catch {
      setSeasonDetailSeasons([])
    } finally {
      setSeasonDetailLoading(false)
    }
  }

  const submitSeasonWish = async (season, parentItem) => {
    const seasonNumber = Number(season.season_number || 0)
    const submitKey = season.lookup_key || `tv:${parentItem.tmdb_id}:${seasonNumber}`
    setSubmittingId(submitKey)
    setError('')
    setNotice('')
    try {
      const wishItem = {
        tmdb_id: parentItem.tmdb_id,
        media_type: 'tv',
        season_number: seasonNumber,
        title: `${parentItem.title} - ${season.name}`,
        original_title: parentItem.original_title,
        release_date: season.air_date,
        year: season.air_date ? season.air_date.slice(0, 4) : '',
        overview: '',
        poster_path: season.poster_path,
        poster_url: season.poster_url,
        backdrop_path: '',
        backdrop_url: '',
      }
      const data = await apiRequest('/public/wishes', {
        method: 'POST',
        body: JSON.stringify({ item: wishItem }),
      })
      const requestRecord = data.request ? normalizeWishItem(data.request) : null
      setNotice(data.message || `${season.name} 已加入想看清单`)
      if (onSuccess) {
        onSuccess()
      }
      if (requestRecord) {
        setSeasonDetailSeasons((prev) =>
          prev.map((current) =>
            Number(current.season_number || 0) === seasonNumber
              ? {
                  ...current,
                  requested: true,
                  request_id: requestRecord.id,
                  request_status: requestRecord.status || 'pending',
                  lookup_key: requestRecord.lookup_key || current.lookup_key,
                }
              : current
          )
        )
        if (wishListOpen) {
          setWishList((prev) => {
            const exists = prev.some((current) => current.lookup_key === requestRecord.lookup_key)
            if (exists) {
              return prev.map((current) => (current.lookup_key === requestRecord.lookup_key ? { ...current, ...requestRecord } : current))
            }
            return [requestRecord, ...prev]
          })
          if (data.request?.created) {
            setWishTotalResults((prev) => prev + 1)
          }
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmittingId('')
    }
  }

  const handleConfirmLibrarySeason = (season, parentItem) => {
    const seasonNumber = Number(season.season_number || 0)
    const wishItem = {
      tmdb_id: parentItem.tmdb_id,
      media_type: 'tv',
      season_number: seasonNumber,
      title: `${parentItem.title} - ${season.name}`,
      original_title: parentItem.original_title,
      release_date: season.air_date,
      year: season.air_date ? season.air_date.slice(0, 4) : '',
      overview: '',
      poster_path: season.poster_path,
      poster_url: season.poster_url,
      backdrop_path: '',
      backdrop_url: '',
      in_library: true,
    }
    setConfirmLibraryItem(wishItem)
  }

  const submitWish = async (item) => {
    const seasonNumber = item.media_type === 'tv' ? Number(item.season_number || 0) : 0
    const submitKey = item.lookup_key || `${item.media_type}:${item.tmdb_id}:${seasonNumber}`
    setSubmittingId(submitKey)
    setError('')
    setNotice('')
    setWishListError('')
    try {
      const data = await apiRequest('/public/wishes', {
        method: 'POST',
        body: JSON.stringify({ item }),
      })
      const requestRecord = data.request ? normalizeWishItem(data.request) : null
      setNotice(data.message || '已加入想看清单')
      if (onSuccess) {
        onSuccess()
      }
      setResults((prev) =>
        prev.map((current) =>
          (current.lookup_key || `${current.media_type}:${current.tmdb_id}:${Number(current.season_number || 0)}`) === requestRecord?.lookup_key
            ? {
                ...current,
                requested: true,
                request_id: data.request?.id,
                request_status: data.request?.status || 'pending',
                lookup_key: requestRecord?.lookup_key || current.lookup_key,
                season_number: requestRecord?.season_number ?? current.season_number,
              }
            : current
        )
      )

      if (requestRecord && wishListOpen) {
        setWishList((prev) => {
          const exists = prev.some((current) => current.lookup_key === requestRecord.lookup_key)
          if (exists) {
            return prev.map((current) =>
              current.lookup_key === requestRecord.lookup_key
                ? { ...current, ...requestRecord }
                : current
            )
          }
          return [requestRecord, ...prev]
        })
        if (data.request?.created) {
          setWishTotalResults((prev) => prev + 1)
        }
      }
    } catch (err) {
      if (wishListOpen) {
        setWishListError(err.message)
      } else {
        setError(err.message)
      }
    } finally {
      setSubmittingId('')
    }
  }

  if (!open) return null

  return (
    <>
      <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4' onClick={onClose}>
        <Card className='flex max-h-[90vh] w-full max-w-7xl flex-col overflow-hidden' onClick={(e) => e.stopPropagation()}>
          <CardHeader className='shrink-0 border-b pb-4'>
            <div className='flex items-start justify-between gap-4'>
              <div>
                <CardTitle>用户求片</CardTitle>
                <p className='mt-1 text-sm text-muted-foreground'>
                  输入关键词后会从 TMDB 搜索电影/电视剧，点击海报即可加入想看清单。
                </p>
                {totalResults ? <p className='mt-1 text-xs text-muted-foreground'>共找到 {totalResults} 条结果</p> : null}
              </div>
              <Button size='icon' variant='ghost' onClick={onClose} title='关闭'>
                <X className='h-4 w-4' />
              </Button>
            </div>
          </CardHeader>
          <CardContent className='flex min-h-0 flex-1 flex-col gap-4 p-6'>
            <form className='flex shrink-0 flex-col gap-2 sm:flex-row' onSubmit={onSearch}>
              <Input
                placeholder='例如：流浪地球、黑镜、鱿鱼游戏'
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
              />
              <Button type='submit' disabled={loading}>
                {loading ? <LoaderCircle className='mr-2 h-4 w-4 animate-spin' /> : <Search className='mr-2 h-4 w-4' />}
                搜索
              </Button>
            </form>

            {error ? <div className='shrink-0 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive'>{error}</div> : null}
            {notice ? <div className='shrink-0 rounded-md border border-primary/30 bg-primary/5 p-3 text-sm text-primary'>{notice}</div> : null}
            {loading ? <p className='shrink-0 text-sm text-muted-foreground'>正在搜索 TMDB...</p> : null}

            <div className='min-h-0 flex-1 overflow-y-auto pr-1'>
              <div className='grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5'>
                {results.map((item) => (
                  <WishPosterCard key={`${item.media_type}-${item.tmdb_id}-search`} item={item} submittingId={submittingId} onSubmit={submitWish} onShowSeasonDetail={showSeasonDetail} onConfirmLibrary={setConfirmLibraryItem} />
                ))}
              </div>

              {!loading && !results.length ? <p className='py-8 text-center text-sm text-muted-foreground'>请输入关键词开始搜索</p> : null}
            </div>

            {!loading && results.length && page < totalPages ? (
              <div className='flex shrink-0 justify-center'>
                <Button type='button' variant='outline' onClick={loadMoreSearch} disabled={loadingMore}>
                  {loadingMore ? <LoaderCircle className='mr-2 h-4 w-4 animate-spin' /> : <ChevronDown className='mr-2 h-4 w-4' />}
                  {loadingMore ? '加载中...' : '加载更多'}
                </Button>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <WishListModal
        open={wishListOpen}
        onClose={() => setWishListOpen(false)}
        items={wishList}
        loading={loadingWishList}
        loadingMore={loadingWishListMore}
        error={wishListError}
        totalResults={wishTotalResults}
        page={wishPage}
        totalPages={wishTotalPages}
        submittingId={submittingId}
        onSubmit={submitWish}
        onLoadMore={loadMoreWishList}
        onShowSeasonDetail={showSeasonDetail}
        onConfirmLibrary={setConfirmLibraryItem}
      />

      <SeasonDetailModal
        open={seasonDetailOpen}
        onClose={() => setSeasonDetailOpen(false)}
        item={seasonDetailItem}
        loading={seasonDetailLoading}
        seasons={seasonDetailSeasons}
        librarySeasonCount={seasonDetailItem?.library_season_count}
        onSubmitSeason={submitSeasonWish}
        onConfirmLibrarySeason={handleConfirmLibrarySeason}
      />

      <div className={`fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4 ${!confirmLibraryItem ? 'hidden' : ''}`} onClick={() => setConfirmLibraryItem(null)}>
        <Card className='flex w-full max-w-md flex-col overflow-hidden sm:max-w-md' onClick={(e) => e.stopPropagation()}>
          <CardHeader className='shrink-0 border-b pb-4'>
            <div className='flex items-start justify-between gap-4'>
              <div>
                <CardTitle>资源已在库中</CardTitle>
                <p className='mt-1 text-sm text-muted-foreground'>该资源已在 Emby 媒体库中，是否再次求片？</p>
              </div>
              <Button size='icon' variant='ghost' onClick={() => setConfirmLibraryItem(null)} title='关闭'>
                <X className='h-4 w-4' />
              </Button>
            </div>
          </CardHeader>
          <CardContent className='py-4'>
            {confirmLibraryItem && (
              <div className='flex items-center gap-3 rounded-lg border p-3'>
                {confirmLibraryItem.poster_url ? (
                  <img src={confirmLibraryItem.poster_url} alt={confirmLibraryItem.title} className='h-16 w-11 rounded object-cover' />
                ) : (
                  <div className='flex h-16 w-11 items-center justify-center rounded bg-muted text-xs text-muted-foreground'>无图</div>
                )}
                <div className='min-w-0 flex-1'>
                  <div className='font-medium truncate'>{confirmLibraryItem.title || confirmLibraryItem.original_title || '未命名内容'}</div>
                  <div className='text-xs text-muted-foreground'>{confirmLibraryItem.media_type === 'movie' ? '电影' : '剧集'} · {confirmLibraryItem.year || ''}</div>
                </div>
              </div>
            )}
          </CardContent>
          <DialogFooter className='gap-2 pb-4 px-6 sm:gap-0'>
            <Button variant='outline' onClick={() => setConfirmLibraryItem(null)}>算了吧</Button>
            <Button onClick={() => {
              if (confirmLibraryItem) {
                submitWish(confirmLibraryItem)
                setConfirmLibraryItem(null)
              }
            }}>继续求片</Button>
          </DialogFooter>
        </Card>
      </div>
    </>
  )
}

export default function HomePage() {
  const [username, setUsername] = useState('')
  const [requestOpen, setRequestOpen] = useState(false)
  const [userSearchOpen, setUserSearchOpen] = useState(false)
  const navigate = useNavigate()

  const { sessions, loading, sessionCountText } = useActiveSessions()

  const onUserSearch = (event) => {
    event.preventDefault()
    if (!username) return
    setUserSearchOpen(false)
    navigate(`/search?username=${encodeURIComponent(username)}`)
  }

  return (
    <>
      <div className='mx-auto max-w-6xl space-y-6 p-4 pb-8 md:p-8'>
        <div className='flex flex-wrap items-center justify-between gap-3'>
          <div>
            <h1 className='text-2xl font-bold'>EmbyQ用户自助中心</h1>
            <p className='mt-1 text-sm text-muted-foreground'>Emby 个人播放记录查询、封禁查询，也可以直接搜索影视内容，加入公共求片清单。</p>
          </div>
        </div>

        <div className='flex gap-2'>
          <Button onClick={() => setUserSearchOpen(true)}>
            <Search className='mr-2 h-4 w-4' /> 用户查询
          </Button>
          <Button onClick={() => setRequestOpen(true)}>
            <Heart className='mr-2 h-4 w-4' /> 求片
          </Button>
        </div>

        <div className='space-y-4'>
          <div className='flex items-center justify-between'>
            <h2 className='text-lg font-semibold'>{sessionCountText}</h2>
            {sessions.length > 0 ? (
              <Badge variant='secondary' className='text-xs'>
                {sessions.length} 人
              </Badge>
            ) : null}
          </div>

          {loading ? (
            <div className='text-center py-8 text-sm text-muted-foreground'>加载中...</div>
          ) : sessions.length > 0 ? (
            <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-3'>
              {sessions.map((session) => (
                <ActiveSessionCard key={session.session_id} session={session} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className='py-8 text-center text-sm text-muted-foreground'>
                暂无正在播放
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <RequestModal open={requestOpen} onClose={() => setRequestOpen(false)} />

      <Dialog open={userSearchOpen} onOpenChange={setUserSearchOpen}>
        <DialogContent className='sm:max-w-lg'>
          <DialogHeader>
            <DialogTitle>用户查询</DialogTitle>
            <DialogDescription>输入 Emby 用户名查询播放记录</DialogDescription>
          </DialogHeader>
          <form className='flex gap-2 mt-4' onSubmit={onUserSearch}>
            <Input
              placeholder='输入 Emby 用户名'
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
            />
            <Button type='submit'>查询</Button>
          </form>
        </DialogContent>
      </Dialog>
    </>
  )
}
