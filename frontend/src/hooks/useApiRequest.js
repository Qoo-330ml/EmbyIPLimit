import { useEffect, useRef, useState } from 'react'
import { apiRequest } from '@/types/api'

export function useApiRequest(path, options = {}) {
  const { immediate = true, deps = [] } = options
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState('')

  const activeRef = useRef(true)

  useEffect(() => {
    activeRef.current = true
    if (!immediate && !path) return

    setLoading(true)
    setError('')

    apiRequest(path)
      .then((result) => {
        if (activeRef.current) {
          setData(result)
        }
      })
      .catch((err) => {
        if (activeRef.current) {
          setError(err.message)
        }
      })
      .finally(() => {
        if (activeRef.current) {
          setLoading(false)
        }
      })

    return () => {
      activeRef.current = false
    }
  }, [path, ...deps])

  const refetch = async (overridePath) => {
    setLoading(true)
    setError('')
    try {
      const result = await apiRequest(overridePath || path)
      setData(result)
      return result
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { data, loading, error, refetch, setData }
}
