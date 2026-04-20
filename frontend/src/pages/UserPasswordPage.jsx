import { useEffect, useState } from 'react'
import { apiRequest } from '@/types/api'
import { EMAIL_PATTERN } from '@/types/format'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

export default function UserProfilePage() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [email, setEmail] = useState('')
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [emailLoading, setEmailLoading] = useState(false)
  const [passwordMessage, setPasswordMessage] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [emailMessage, setEmailMessage] = useState('')
  const [emailError, setEmailError] = useState('')

  useEffect(() => {
    apiRequest('/user/profile')
      .then((data) => {
        if (data.email) {
          setEmail(data.email)
        }
      })
      .catch(() => {})
  }, [])

  const handlePasswordSubmit = async (e) => {
    e.preventDefault()
    setPasswordError('')
    setPasswordMessage('')
    if (!currentPassword || !newPassword) {
      setPasswordError('请填写所有字段')
      return
    }
    if (newPassword.length < 4) {
      setPasswordError('新密码至少4个字符')
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('两次输入的密码不一致')
      return
    }
    setPasswordLoading(true)
    try {
      await apiRequest('/user/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      })
      setPasswordMessage('密码修改成功')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setPasswordError(err.message)
    } finally {
      setPasswordLoading(false)
    }
  }

  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    setEmailError('')
    setEmailMessage('')
    if (!email) {
      setEmailError('邮箱不能为空')
      return
    }
    if (!EMAIL_PATTERN.test(email)) {
      setEmailError('邮箱格式不正确')
      return
    }
    setEmailLoading(true)
    try {
      await apiRequest('/user/update-email', {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
      setEmailMessage('邮箱更新成功')
    } catch (err) {
      setEmailError(err.message)
    } finally {
      setEmailLoading(false)
    }
  }

  return (
    <>
      <Header>
        <h1 className='text-lg font-medium'>修改信息</h1>
      </Header>
      <Main>
        <Card className='mb-6'>
          <CardHeader>
            <CardTitle>邮箱设置</CardTitle>
            <CardDescription>设置你的联系邮箱</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleEmailSubmit} className='grid gap-4 max-w-md'>
              <div className='grid gap-2'>
                <Label htmlFor='email'>邮箱</Label>
                <Input id='email' type='email' value={email} onChange={(e) => setEmail(e.target.value)} disabled={emailLoading} placeholder='请输入邮箱地址' />
              </div>
              {emailError && <p className='text-sm text-destructive'>{emailError}</p>}
              {emailMessage && <p className='text-sm text-green-600 dark:text-green-400'>{emailMessage}</p>}
              <Button type='submit' disabled={emailLoading}>保存</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>修改密码</CardTitle>
            <CardDescription>更新你的账号密码</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handlePasswordSubmit} className='grid gap-4 max-w-md'>
              <div className='grid gap-2'>
                <Label htmlFor='current'>当前密码</Label>
                <Input id='current' type='password' value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} disabled={passwordLoading} />
              </div>
              <div className='grid gap-2'>
                <Label htmlFor='new'>新密码</Label>
                <Input id='new' type='password' value={newPassword} onChange={(e) => setNewPassword(e.target.value)} disabled={passwordLoading} />
              </div>
              <div className='grid gap-2'>
                <Label htmlFor='confirm'>确认新密码</Label>
                <Input id='confirm' type='password' value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} disabled={passwordLoading} />
              </div>
              {passwordError && <p className='text-sm text-destructive'>{passwordError}</p>}
              {passwordMessage && <p className='text-sm text-green-600 dark:text-green-400'>{passwordMessage}</p>}
              <Button type='submit' disabled={passwordLoading}>保存</Button>
            </form>
          </CardContent>
        </Card>
      </Main>
    </>
  )
}
