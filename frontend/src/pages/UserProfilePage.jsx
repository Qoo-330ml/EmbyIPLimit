import { useEffect, useState } from 'react'
import { apiRequest } from '@/types/api'
import { getUserStatus } from '@/types/format'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function UserProfilePage() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiRequest('/user/profile')
      .then(setProfile)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const status = profile ? getUserStatus(profile) : null

  return (
    <>
      <Header>
        <h1 className='text-lg font-medium'>个人信息</h1>
      </Header>
      <Main>
        <Card>
          <CardHeader>
            <CardTitle>账号信息</CardTitle>
            <CardDescription>你的账号详细信息</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className='text-muted-foreground'>加载中...</div>
            ) : profile ? (
              <div className='grid gap-4'>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-muted-foreground'>用户名</span>
                  <span className='font-medium'>{profile.username}</span>
                </div>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-muted-foreground'>用户 ID</span>
                  <span className='font-mono text-sm'>{profile.user_id}</span>
                </div>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-muted-foreground'>邮箱</span>
                  <span className='font-medium'>{profile.email || <span className='text-muted-foreground'>未设置</span>}</span>
                </div>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-muted-foreground'>所属分组</span>
                  <div className='flex gap-1'>
                    {profile.groups?.map((g) => (
                      <Badge key={g} variant='secondary'>{g}</Badge>
                    ))}
                    {(!profile.groups || profile.groups.length === 0) && <span className='text-sm text-muted-foreground'>无</span>}
                  </div>
                </div>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-muted-foreground'>到期时间</span>
                  <span className='text-sm'>
                    {profile.expiry_date
                      ? profile.expiry_date === 'never'
                        ? <Badge variant='outline'>永不过期</Badge>
                        : new Date(profile.expiry_date).toLocaleDateString('zh-CN')
                      : <span className='text-muted-foreground'>未设置</span>}
                  </span>
                </div>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-muted-foreground'>状态</span>
                  <Badge variant={status?.variant}>{status?.label}</Badge>
                </div>
              </div>
            ) : (
              <div className='text-muted-foreground'>无法加载信息</div>
            )}
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
