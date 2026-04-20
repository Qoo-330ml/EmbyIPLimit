import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogIn } from 'lucide-react'

import { Button } from '@/components/ui/button'

const DEFAULT_POSTERS = [
  { url: 'https://image.tmdb.org/t/p/original/2I1OFQJ0L9T0dpU6FobKFWV2PxX.jpg', title: '挽救计划' },
  { url: 'https://image.tmdb.org/t/p/original/tyQo080tijexyUHBvWPwQt26bZa.jpg', title: 'Spider-Man: No Way Home' },
  { url: 'https://image.tmdb.org/t/p/original/1RgPyOhN4DRs225BGTlHJqCudII.jpg', title: '鬼灭之刃：无限城篇 第一章 猗窝座再袭' },
  { url: 'https://image.tmdb.org/t/p/original/65BTgbR7w8g5h8PlNwUgRVWqPyQ.jpg', title: '星际穿越' },
  { url: 'https://image.tmdb.org/t/p/original/pO1SnM5a1fEsYrFaVZW78Wb0zRJ.jpg', title: '咱们裸熊：电影版' },
]

export default function LandingPage() {
  const navigate = useNavigate()
  const [posters, setPosters] = useState(DEFAULT_POSTERS)
  const [current, setCurrent] = useState(0)
  const [transitioning, setTransitioning] = useState(false)
  const timerRef = useRef(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    const fetchPosters = async () => {
      try {
        const resp = await fetch('/api/public/landing-posters')
        if (resp.ok) {
          const data = await resp.json()
          if (data && data.length > 0) {
            setPosters(data)
          }
        }
      } catch {
        // 使用默认海报
      }
    }
    fetchPosters()
  }, [])

  const startTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    if (posters.length === 0) return
    timerRef.current = setInterval(() => {
      if (!mountedRef.current) return
      setTransitioning(true)
      setTimeout(() => {
        if (!mountedRef.current) return
        setCurrent((prev) => (prev + 1) % posters.length)
        setTransitioning(false)
      }, 800)
    }, 10000)
  }, [posters.length])

  useEffect(() => {
    mountedRef.current = true
    startTimer()
    return () => {
      mountedRef.current = false
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [startTimer])

  const goTo = (index) => {
    if (index === current) return
    setTransitioning(true)
    setTimeout(() => {
      setCurrent(index)
      setTransitioning(false)
    }, 800)
    startTimer()
  }

  if (posters.length === 0) {
    return (
      <div className='relative h-screen w-screen overflow-hidden bg-black'>
        <div className='absolute left-6 top-6 z-20 flex flex-col gap-3'>
          <div className='flex items-center gap-3 rounded-xl bg-black/30 px-4 py-3 backdrop-blur-md'>
            <img src='/favicon.svg' alt='EmbyQ' className='h-8 shrink-0' />
            <span className='text-sm font-medium tracking-wide text-white'>
              EmbyQ，你私人影视的用户管理中心
            </span>
          </div>
          <Button size='lg' className='w-32 gap-2 bg-primary/90 px-4 text-sm backdrop-blur-sm hover:bg-primary' onClick={() => navigate('/login')}>
            <LogIn className='h-5 w-5' />
            登录
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className='relative h-screen w-screen overflow-hidden bg-black'>
      {posters.map((poster, index) => (
        <div
          key={poster.title || index}
          className='absolute inset-0 bg-cover bg-center transition-opacity duration-[800ms] ease-in-out'
          style={{
            backgroundImage: `url(${poster.url})`,
            opacity: index === current ? (transitioning ? 0 : 1) : 0,
            zIndex: index === current ? 1 : 0,
          }}
        />
      ))}

      <div className='absolute left-6 top-6 z-20 flex flex-col gap-3'>
        <div className='flex items-center gap-3 rounded-xl bg-black/30 px-4 py-3 backdrop-blur-md'>
          <img src='/favicon.svg' alt='EmbyQ' className='h-8 shrink-0' />
          <span className='text-sm font-medium tracking-wide text-white'>
            EmbyQ，你私人影视的用户管理中心
          </span>
        </div>
        <Button size='lg' className='w-32 gap-2 bg-primary/90 px-4 text-sm backdrop-blur-sm hover:bg-primary' onClick={() => navigate('/login')}>
          <LogIn className='h-5 w-5' />
          登录
        </Button>
      </div>

      <div className='absolute bottom-8 left-1/2 z-20 flex -translate-x-1/2 gap-2'>
        {posters.map((_, index) => (
          <button
            key={index}
            type='button'
            onClick={() => goTo(index)}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              index === current ? 'w-8 bg-white' : 'w-4 bg-white/40 hover:bg-white/60'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
