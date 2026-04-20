import { useCallback, useState } from 'react'
import { apiRequest } from '@/types/api'

export function usePaginatedData(urlTemplate, options = {}) {
  const { pageSize = 25 } = options
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalResults, setTotalResults] = useState(0)

  const load = useCallback(async (pageNum = 1, append = false) => {
    if (append) {
      setLoadingMore(true)
    } else {
      setLoading(true)
    }
    setError('')
    try {
      const url = typeof urlTemplate === 'function'
        ? urlTemplate(pageNum, pageSize)
        : `${urlTemplate}?page=${pageNum}&page_size=${pageSize}`
      const data = await apiRequest(url)
      setItems((prev) => (append ? [...prev, ...(data.requests || data.items || [])] : (data.requests || data.items || [])))
      setPage(data.page || pageNum)
      setTotalPages(data.total_pages || 1)
      setTotalResults(data.total_results || 0)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [urlTemplate, pageSize])

  const loadMore = useCallback(() => {
    if (page < totalPages) {
      load(page + 1, true)
    }
  }, [page, totalPages, load])

  const reset = useCallback(() => {
    setItems([])
    setPage(1)
    setTotalPages(1)
    setTotalResults(0)
    setError('')
  }, [])

  return {
    items,
    loading,
    loadingMore,
    error,
    page,
    totalPages,
    totalResults,
    load,
    loadMore,
    reset,
    setItems,
    setError,
  }
}
