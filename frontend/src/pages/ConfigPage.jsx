import { useEffect, useState } from 'react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { apiRequest } from '@/types/api'

export default function ConfigPage() {
  const [config, setConfig] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [testingWebhook, setTestingWebhook] = useState(false)
  const [webhookNotice, setWebhookNotice] = useState('')
  const [syncing, setSyncing] = useState(false)
  const [syncNotice, setSyncNotice] = useState('')
  const [testingEmail, setTestingEmail] = useState(false)
  const [emailNotice, setEmailNotice] = useState('')

  useEffect(() => {
    apiRequest('/admin/config').then((data) => setConfig(data.config)).catch((err) => setError(err.message))
  }, [])

  const update = (path, value) => {
    setConfig((prev) => {
      const next = structuredClone(prev)
      let cursor = next
      for (let i = 0; i < path.length - 1; i += 1) cursor = cursor[path[i]]
      cursor[path[path.length - 1]] = value
      return next
    })
  }

  const updateWhitelistItem = (index, value) => {
    const current = [...(config?.security?.whitelist || [])]
    current[index] = value
    update(['security', 'whitelist'], current)
  }

  const addWhitelistItem = () => {
    const current = [...(config?.security?.whitelist || [])]
    current.push('')
    update(['security', 'whitelist'], current)
  }

  const removeWhitelistItem = (index) => {
    const current = [...(config?.security?.whitelist || [])]
    current.splice(index, 1)
    update(['security', 'whitelist'], current)
  }

  const onSave = async () => {
    setSaving(true); setNotice(''); setError('')
    const nextConfig = structuredClone(config)
    nextConfig.security.whitelist = (nextConfig.security.whitelist || []).map((v) => String(v || '').trim()).filter(Boolean)
    try {
      await apiRequest('/admin/config', { method: 'PUT', body: JSON.stringify({ config: nextConfig }) })
      setNotice('配置已保存'); setConfig(nextConfig)
    } catch (err) { setError(err.message) } finally { setSaving(false) }
  }

  const onSyncShadow = async () => {
    setSyncing(true); setSyncNotice('')
    try {
      const result = await apiRequest('/admin/shadow/sync', { method: 'POST' })
      const { movies, series } = result.result || {}
      setSyncNotice(`同步完成：电影 ${movies?.synced || 0} 部（新增）, 剧集 ${series?.synced || 0} 部（新增）`)
    } catch (err) { setSyncNotice(`同步失败：${err.message}`) } finally { setSyncing(false) }
  }

  const onTestWebhook = async () => {
    setTestingWebhook(true); setWebhookNotice(''); setError('')
    const nextConfig = structuredClone(config)
    nextConfig.security.whitelist = (nextConfig.security.whitelist || []).map((v) => String(v || '').trim()).filter(Boolean)
    try {
      await apiRequest('/admin/config', { method: 'PUT', body: JSON.stringify({ config: nextConfig }) })
      setConfig(nextConfig)
      await apiRequest('/admin/webhook/test', { method: 'POST' })
      setWebhookNotice('测试通知已发送')
    } catch (err) { setWebhookNotice(`测试失败：${err.message}`) } finally { setTestingWebhook(false) }
  }

  const onTestEmail = async () => {
    setTestingEmail(true); setEmailNotice('')
    const nextConfig = structuredClone(config)
    nextConfig.security.whitelist = (nextConfig.security.whitelist || []).map((v) => String(v || '').trim()).filter(Boolean)
    try {
      await apiRequest('/admin/config', { method: 'PUT', body: JSON.stringify({ config: nextConfig }) })
      setConfig(nextConfig)
      const result = await apiRequest('/admin/email/test', { method: 'POST' })
      setEmailNotice(result.message || '测试邮件已发送')
    } catch (err) { setEmailNotice(`测试失败：${err.message}`) } finally { setTestingEmail(false) }
  }

  if (!config) return <><Header /><Main><div className='text-muted-foreground'>加载配置中...</div></Main></>

  return (
    <>
      <Header><h1 className='text-lg font-medium'>配置管理</h1></Header>
      <Main>
        <div className='grid gap-6'>
          <Card>
            <CardHeader><CardTitle>Emby 配置</CardTitle><CardDescription>Emby 服务器连接与同步设置</CardDescription></CardHeader>
            <CardContent className='grid gap-4 md:grid-cols-2'>
              <div className='grid gap-2'><Label>Emby服务器地址（内网）</Label><Input value={config.emby.server_url || ''} onChange={(e) => update(['emby', 'server_url'], e.target.value)} /></div>
              <div className='grid gap-2'><Label>Emby服务器外网地址</Label><Input value={config.emby.external_url || ''} onChange={(e) => update(['emby', 'external_url'], e.target.value)} /></div>
              <div className='grid gap-2'><Label>EmbyQ外网地址（用于发送邀请链接）</Label><Input value={config.service?.external_url || ''} onChange={(e) => update(['service', 'external_url'], e.target.value)} /></div>
              <div className='grid gap-2'><Label>Emby API Key</Label><Input value={config.emby.api_key || ''} onChange={(e) => update(['emby', 'api_key'], e.target.value)} /></div>
              <div className='grid gap-2'><Label>检查间隔(秒)</Label><Input type='number' value={config.monitor?.check_interval || 10} onChange={(e) => update(['monitor', 'check_interval'], Number(e.target.value || 10))} /></div>
              <div className='flex items-end gap-2'><Button onClick={onSyncShadow} disabled={syncing}>{syncing ? '同步中...' : '同步影子库'}</Button>{syncNotice && <span className='text-sm text-muted-foreground'>{syncNotice}</span>}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>求片功能</CardTitle></CardHeader>
            <CardContent className='grid gap-4 md:grid-cols-2'>
              <label className='flex items-center gap-2 text-sm'><Checkbox checked={Boolean(config.guest_request?.enabled)} onChange={(e) => update(['guest_request', 'enabled'], e.target.checked)} /> 启用求片功能</label>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>TMDB搜索</CardTitle></CardHeader>
            <CardContent className='grid gap-4 md:grid-cols-2'>
              <label className='flex items-center gap-2 text-sm'><Checkbox checked={Boolean(config.tmdb?.enabled)} onChange={(e) => update(['tmdb', 'enabled'], e.target.checked)} /> 启用TMDB搜索</label>
              <label className='flex items-center gap-2 text-sm'><Checkbox checked={Boolean(config.tmdb?.include_adult)} onChange={(e) => update(['tmdb', 'include_adult'], e.target.checked)} /> 搜索时包含成人内容</label>
              <div className='grid gap-2'><Label>TMDB API Key</Label><Input value={config.tmdb?.api_key || ''} onChange={(e) => update(['tmdb', 'api_key'], e.target.value)} /></div>
              <div className='grid gap-2'><Label>TMDB 语言</Label><Input value={config.tmdb?.language || 'zh-CN'} onChange={(e) => update(['tmdb', 'language'], e.target.value)} /></div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>IP 归属地解析</CardTitle></CardHeader>
            <CardContent className='space-y-4'>
              <label className='flex items-start gap-2 text-sm'><Checkbox checked={Boolean(config.ip_location?.use_geocache)} onChange={(e) => update(['ip_location', 'use_geocache'], e.target.checked)} className='mt-1' /><div className='flex-1'><div className='font-medium'>启用自建库解析</div><div className='mt-1 text-xs text-muted-foreground'>默认使用IP138解析归属地，启用后会切换到优先自建归属地库，并清空已有解析缓存。</div></div></label>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>系统代理</CardTitle></CardHeader>
            <CardContent className='space-y-4'>
              <label className='flex items-center gap-2 text-sm'><Checkbox checked={Boolean(config.proxy?.enabled)} onChange={(e) => update(['proxy', 'enabled'], e.target.checked)} /> 启用代理</label>
              <div className='grid gap-2'><Label>代理地址</Label><Input placeholder='http://127.0.0.1:7890 或 socks5://127.0.0.1:7890' value={config.proxy?.url || ''} onChange={(e) => update(['proxy', 'url'], e.target.value)} /></div>
              <p className='text-xs text-muted-foreground'>设置后 TMDB 搜索请求将通过指定代理转发。支持 http、https、socks5 协议。</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>邮件通知</CardTitle><CardDescription>配置SMTP邮件发送，用于向用户发送求片状态更新和评论通知</CardDescription></CardHeader>
            <CardContent className='grid gap-4 md:grid-cols-2'>
              <label className='flex items-center gap-2 text-sm md:col-span-2'><Checkbox checked={Boolean(config.email?.enabled)} onChange={(e) => update(['email', 'enabled'], e.target.checked)} /> 启用邮件通知</label>
              <div className='grid gap-2'><Label>SMTP服务器</Label><Input value={config.email?.smtp_server || 'smtp.qq.com'} onChange={(e) => update(['email', 'smtp_server'], e.target.value)} /></div>
              <div className='grid gap-2'><Label>SMTP端口</Label><Input type='number' value={config.email?.smtp_port || 465} onChange={(e) => update(['email', 'smtp_port'], Number(e.target.value || 465))} /></div>
              <div className='grid gap-2'><Label>发件人邮箱</Label><Input type='email' placeholder='your@qq.com' value={config.email?.sender_email || ''} onChange={(e) => update(['email', 'sender_email'], e.target.value)} /></div>
              <div className='grid gap-2'><Label>邮箱密码/授权码</Label><Input type='password' placeholder='QQ邮箱请使用授权码' value={config.email?.sender_password || ''} onChange={(e) => update(['email', 'sender_password'], e.target.value)} /></div>
              <label className='flex items-center gap-2 text-sm'><Checkbox checked={Boolean(config.email?.use_ssl)} onChange={(e) => update(['email', 'use_ssl'], e.target.checked)} /> 使用SSL</label>
              <div className='flex items-end gap-2'><Button type='button' variant='secondary' onClick={onTestEmail} disabled={testingEmail || saving}>{testingEmail ? '测试中...' : '测试邮件'}</Button>{emailNotice && <span className='text-sm text-muted-foreground'>{emailNotice}</span>}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>落地页轮播图</CardTitle><CardDescription>选择落地页轮播图的图片来源，每天凌晨2点自动拉取最新图片</CardDescription></CardHeader>
            <CardContent className='space-y-4'>
              <div className='grid gap-2'>
                <Label>图片来源</Label>
                <Select value={config.landing?.source || 'default'} onValueChange={(v) => update(['landing', 'source'], v)}>
                  <SelectTrigger className='w-64'><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value='default'>默认（硬编码）</SelectItem>
                    <SelectItem value='tmdb'>TMDB 本周趋势</SelectItem>
                    <SelectItem value='emby'>Emby 服务器</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {config.landing?.source === 'tmdb' && (
                <p className='text-xs text-muted-foreground'>需要配置 TMDB API Key（见上方 TMDB 搜索配置），将获取本周趋势影视的横版剧照作为轮播图。</p>
              )}
              {config.landing?.source === 'emby' && (
                <p className='text-xs text-muted-foreground'>需要配置 Emby 服务器连接（见上方 Emby 配置），将获取 Emby 媒体库中的横版背景图作为轮播图。</p>
              )}
              {config.landing?.source === 'default' && (
                <p className='text-xs text-muted-foreground'>使用内置的默认海报图片，无需额外配置。</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>自动封禁</CardTitle></CardHeader>
            <CardContent className='space-y-4'>
              <div className='grid gap-4 md:grid-cols-2'>
                <div className='grid gap-2'><Label>告警阈值</Label><Input type='number' value={config.notifications.alert_threshold || 2} onChange={(e) => update(['notifications', 'alert_threshold'], Number(e.target.value || 2))} /></div>
                <label className='flex items-center gap-2 pt-8 text-sm'><Checkbox checked={Boolean(config.notifications.enable_alerts)} onChange={(e) => update(['notifications', 'enable_alerts'], e.target.checked)} /> 启用异常封禁</label>
              </div>
              <div className='space-y-2'>
                <div className='flex items-center justify-between'><Label>白名单用户</Label><Button size='sm' variant='secondary' onClick={addWhitelistItem}>添加</Button></div>
                <div className='space-y-2'>
                  {(config.security.whitelist || []).map((name, idx) => (
                    <div key={`wl-${idx}`} className='flex gap-2'><Input value={name} onChange={(e) => updateWhitelistItem(idx, e.target.value)} /><Button size='sm' variant='destructive' onClick={() => removeWhitelistItem(idx)}>删除</Button></div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Webhook 配置</CardTitle></CardHeader>
            <CardContent className='grid gap-4 md:grid-cols-2'>
              <label className='flex items-center gap-2 text-sm md:col-span-2'><Checkbox checked={Boolean(config.webhook?.enabled)} onChange={(e) => update(['webhook', 'enabled'], e.target.checked)} /> 启用 Webhook</label>
              <div className='grid gap-2'><Label>Webhook URL</Label><Input value={config.webhook?.url || ''} onChange={(e) => update(['webhook', 'url'], e.target.value)} /></div>
              <div className='grid gap-2'><Label>超时(秒)</Label><Input type='number' value={config.webhook?.timeout || 10} onChange={(e) => update(['webhook', 'timeout'], Number(e.target.value || 10))} /></div>
              <div className='grid gap-2'><Label>重试次数</Label><Input type='number' value={config.webhook?.retry_attempts || 3} onChange={(e) => update(['webhook', 'retry_attempts'], Number(e.target.value || 3))} /></div>
              <div className='grid gap-2 md:col-span-2'>
                <div className='flex items-center justify-between gap-3'><Label>Webhook Body (YAML 或 JSON)</Label><Button type='button' variant='secondary' onClick={onTestWebhook} disabled={testingWebhook || saving}>{testingWebhook ? '测试中...' : '测试 Webhook'}</Button></div>
                <Textarea className='min-h-48 font-mono' value={typeof config.webhook?.body === 'string' ? config.webhook.body : config.webhook?.body ? JSON.stringify(config.webhook.body, null, 2) : ''} onChange={(e) => update(['webhook', 'body'], e.target.value)} />
                {webhookNotice && <p className='text-sm text-muted-foreground'>{webhookNotice}</p>}
              </div>
            </CardContent>
          </Card>

          {error && <p className='text-sm text-destructive'>{error}</p>}
          {notice && <p className='text-sm text-primary'>{notice}</p>}
          <Button onClick={onSave} disabled={saving}>{saving ? '保存中...' : '保存配置'}</Button>
        </div>
      </Main>
    </>
  )
}
