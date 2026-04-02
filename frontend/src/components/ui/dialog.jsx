import { X } from 'lucide-react'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

export function Dialog({ open, onClose, children }) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  if (!open) return null

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50' onClick={onClose}>
      <Card className='w-full max-w-md mx-4' onClick={(e) => e.stopPropagation()}>
        <CardContent className='p-6'>
          {children}
        </CardContent>
      </Card>
    </div>
  )
}

export function DialogHeader({ children }) {
  return <div className='mb-4'>{children}</div>
}

export function DialogTitle({ children }) {
  return <h2 className='text-lg font-semibold'>{children}</h2>
}

export function DialogDescription({ children }) {
  return <p className='mt-1 text-sm text-muted-foreground'>{children}</p>
}

export function DialogClose({ onClose }) {
  return (
    <Button variant='ghost' size='icon' className='absolute right-4 top-4' onClick={onClose}>
      <X className='h-4 w-4' />
    </Button>
  )
}