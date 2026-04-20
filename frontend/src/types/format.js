export function formatDuration(seconds) {
  if (!seconds && seconds !== 0) return '-'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}分${s}秒`
}

export function getUserStatus(user) {
  if (user.is_disabled) return { label: '禁用', variant: 'destructive' }
  if (user.is_expired) return { label: '已到期', variant: 'secondary' }
  return { label: '正常', variant: 'default' }
}

export function formatTime(timeStr) {
  if (!timeStr) return ''
  try {
    const d = new Date(timeStr.replace(' ', 'T'))
    if (isNaN(d.getTime())) return timeStr
    const now = new Date()
    const diffMs = now - d
    const diffMin = Math.floor(diffMs / 60000)
    if (diffMin < 1) return '刚刚'
    if (diffMin < 60) return `${diffMin}分钟前`
    const diffHour = Math.floor(diffMin / 60)
    if (diffHour < 24) return `${diffHour}小时前`
    const diffDay = Math.floor(diffHour / 24)
    if (diffDay < 30) return `${diffDay}天前`
    return `${d.getMonth() + 1}月${d.getDate()}日`
  } catch {
    return timeStr
  }
}

export const WISH_STATUS_LABELS = {
  pending: '待处理',
  approved: '已采纳',
  rejected: '已拒绝',
}

export const EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
