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
