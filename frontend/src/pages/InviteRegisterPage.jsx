import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Loader2, CheckCircle2 } from 'lucide-react'
import { AuthLayout } from '@/components/layout/auth-layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiRequest } from '@/types/api'
import { EMAIL_PATTERN } from '@/types/format'

export default function InviteRegisterPage() {
  const { code } = useParams()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [verifying, setVerifying] = useState(true)
  const [error, setError] = useState('')
  const [inviteInfo, setInviteInfo] = useState(null)
  const [success, setSuccess] = useState(false)
  const [redirectUrl, setRedirectUrl] = useState('')

  useEffect(() => {
    apiRequest(`/public/invite/${code}`)
      .then((data) => {
        setInviteInfo(data)
        const invite = data?.invite
        if (invite) {
          const inviteEmail = invite.target_email || ''
          const isFirstUse = Number(invite.used_count || 0) === 0
          if (isFirstUse && inviteEmail) {
            setEmail(inviteEmail)
          }
        }
      })
      .catch((err) => {
        setError(err.message)
      })
      .finally(() => setVerifying(false))
  }, [code])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    const trimmedEmail = email.trim()
    if (trimmedEmail) {
      if (!EMAIL_PATTERN.test(trimmedEmail)) {
        setError('邮箱格式不正确')
        setLoading(false)
        return
      }
    }
    try {
      const data = await apiRequest(`/public/invite/${code}/register`, {
        method: 'POST',
        body: JSON.stringify({ username, password: password || username, email: trimmedEmail || undefined }),
      })
      setSuccess(true)
      if (data.redirect_url) setRedirectUrl(data.redirect_url)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (verifying) {
    return (
      <AuthLayout>
        <div className='flex items-center justify-center'>
          <Loader2 className='size-6 animate-spin text-muted-foreground' />
        </div>
      </AuthLayout>
    )
  }

  if (!inviteInfo) {
    return (
      <AuthLayout>
        <Card>
          <CardHeader className='text-center'>
            <CardTitle className='text-2xl text-destructive'>邀请链接无效</CardTitle>
            <CardDescription>{error || '该邀请链接不存在或已失效'}</CardDescription>
          </CardHeader>
        </Card>
      </AuthLayout>
    )
  }

  if (success) {
    return (
      <AuthLayout>
        <Card>
          <CardHeader className='text-center'>
            <div className='mx-auto mb-2 flex size-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900'>
              <CheckCircle2 className='size-6 text-green-600 dark:text-green-400' />
            </div>
            <CardTitle className='text-2xl'>注册成功</CardTitle>
            <CardDescription>你的账号已创建</CardDescription>
          </CardHeader>
          <CardContent className='grid gap-4'>
            {redirectUrl ? (
              <Button className='w-full' onClick={() => window.location.href = redirectUrl}>前往 Emby</Button>
            ) : (
              <Button className='w-full' onClick={() => navigate('/login')}>前往登录</Button>
            )}
          </CardContent>
        </Card>
      </AuthLayout>
    )
  }

  const invite = inviteInfo?.invite
  const isFirstUse = invite && Number(invite.used_count || 0) === 0
  const hasInviteEmail = invite?.target_email

  return (
    <AuthLayout>
      <Card>
        <CardHeader className='text-center'>
          <CardTitle className='text-2xl'>注册账号</CardTitle>
          <CardDescription>通过邀请链接创建你的账号</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className='grid gap-4'>
            <div className='grid gap-2'>
              <Label htmlFor='username'>用户名</Label>
              <Input id='username' type='text' placeholder='请输入用户名' value={username} onChange={(e) => setUsername(e.target.value)} required disabled={loading} />
            </div>
            <div className='grid gap-2'>
              <Label htmlFor='password'>密码（留空则与用户名相同）</Label>
              <Input id='password' type='password' placeholder='请输入密码' value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} />
            </div>
            <div className='grid gap-2'>
              <Label htmlFor='email'>邮箱（选填）</Label>
              <Input id='email' type='email' placeholder='请输入邮箱地址' value={email} onChange={(e) => setEmail(e.target.value)} disabled={loading} />
              {isFirstUse && hasInviteEmail && (
                <p className='text-xs text-muted-foreground'>此邮箱由邀请提供者预设，如需修改可直接编辑</p>
              )}
            </div>
            {error && <p className='text-sm text-destructive'>{error}</p>}
            <Button type='submit' className='w-full' disabled={loading}>
              {loading && <Loader2 className='animate-spin' />}
              注册
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthLayout>
  )
}
