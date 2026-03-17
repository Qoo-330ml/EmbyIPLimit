import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { apiRequest } from '@/types/api'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const onSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
      navigate('/admin')
    } catch (err) {
      setError(err.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='flex min-h-screen items-center justify-center p-4'>
      <Card className='w-full max-w-md'>
        <CardHeader>
          <CardTitle>管理员登录</CardTitle>
          <CardDescription>登录 EmbyIPLimit 管理后台</CardDescription>
        </CardHeader>
        <CardContent>
          <form className='space-y-4' onSubmit={onSubmit}>
            <div className='space-y-2'>
              <label className='text-sm text-muted-foreground'>用户名</label>
              <Input value={username} onChange={(e) => setUsername(e.target.value)} required />
            </div>
            <div className='space-y-2'>
              <label className='text-sm text-muted-foreground'>密码</label>
              <Input
                type='password'
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error ? <p className='text-sm text-destructive'>{error}</p> : null}
            <Button type='submit' className='w-full' disabled={loading}>
              {loading ? '登录中...' : '登录'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
