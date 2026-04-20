import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { AuthLayout } from '@/components/layout/auth-layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiRequest } from '@/types/api'

export default function LoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
      if (data.user?.is_admin) {
        navigate('/app/admin/users')
      } else {
        navigate('/app/user/profile')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <Card>
        <CardHeader className='text-center'>
          <CardTitle className='text-2xl'>欢迎回来</CardTitle>
          <CardDescription>输入你的账号信息登录</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className='grid gap-4'>
            <div className='grid gap-2'>
              <Label htmlFor='username'>用户名</Label>
              <Input id='username' type='text' placeholder='请输入用户名' value={username} onChange={(e) => setUsername(e.target.value)} required disabled={loading} />
            </div>
            <div className='grid gap-2'>
              <Label htmlFor='password'>密码</Label>
              <Input id='password' type='password' placeholder='请输入密码' value={password} onChange={(e) => setPassword(e.target.value)} required disabled={loading} />
            </div>
            {error && <p className='text-sm text-destructive'>{error}</p>}
            <Button type='submit' className='w-full' disabled={loading}>
              {loading && <Loader2 className='animate-spin' />}
              登录
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthLayout>
  )
}
