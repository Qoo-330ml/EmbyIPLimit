import * as React from 'react'

import { cn } from '@/lib/utils'

function Checkbox({ className, checked, onChange, ...props }) {
  return (
    <input
      type='checkbox'
      checked={checked}
      onChange={onChange}
      className={cn('h-4 w-4 rounded border border-input accent-primary', className)}
      {...props}
    />
  )
}

export { Checkbox }
