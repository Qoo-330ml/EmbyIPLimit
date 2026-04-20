import { useCallback, useEffect, useMemo, useState } from 'react'
import { CalendarPlus, Link2, Lock, LockOpen, UserPlus, Activity, Circle, Server, XCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import UserIdentity from '@/components/UserIdentity'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { apiRequest } from '@/types/api'
import { getUserStatus } from '@/types/format'
import { useActiveSessions, ActiveSessionCard } from '@/hooks/useActiveSessions'

export default function AdminPage() {
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState({ total: 0, disabled: 0, expired: 0, never_expire: 0 })
  const [selected, setSelected] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [customDays, setCustomDays] = useState('')
  const [notice, setNotice] = useState('')
  const [editingUser, setEditingUser] = useState(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [inviteOpen, setInviteOpen] = useState(false)
  const [allGroups, setAllGroups] = useState([])
  const [createUsername, setCreateUsername] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [templateUserId, setTemplateUserId] = useState('')
  const [createGroupIds, setCreateGroupIds] = useState([])
  const [inviteHours, setInviteHours] = useState('24')
  const [inviteCount, setInviteCount] = useState('1')
  const [inviteGroupId, setInviteGroupId] = useState('')
  const [inviteExpiryDate, setInviteExpiryDate] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteUrl, setInviteUrl] = useState('')
  const [inviteList, setInviteList] = useState([])
  const [copiedCode, setCopiedCode] = useState(null)
  const [expiryDate, setExpiryDate] = useState('')
  const [neverExpire, setNeverExpire] = useState(false)
  const [alertThreshold, setAlertThreshold] = useState('')
  const [batchThreshold, setBatchThreshold] = useState('')
  const [serverInfo, setServerInfo] = useState(null)
  const navigate = useNavigate()

  const { sessions, loading: sessionsLoading, sessionCountText } = useActiveSessions()

  const selectedIds = useMemo(
    () => Object.entries(selected).filter(([, checked]) => checked).map(([id]) => id),
    [selected]
  )

  const loadUsers = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest('/admin/users')
      setUsers(data.users || [])
      setStats(data.stats || { total: 0, disabled: 0, expired: 0, never_expire: 0 })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [navigate])

  const loadGroups = useCallback(async () => {
    try {
      const groupData = await apiRequest('/admin/groups')
      setAllGroups(groupData.groups || [])
    } catch { /* ignore */ }
  }, [])

  const loadInvites = useCallback(async () => {
    try {
      const data = await apiRequest('/admin/invites')
      setInviteList(data.invites || [])
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { loadUsers(); loadGroups(); loadInvites() }, [loadGroups, loadInvites, loadUsers])

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const data = await apiRequest('/public/server-info')
        if (active) setServerInfo(data)
      } catch {
        if (active) setServerInfo(null)
      }
    }
    load()
    const timer = setInterval(() => load(), 30000)
    return () => { active = false; if (timer) clearInterval(timer) }
  }, [])

  const handleCopyInvite = async (url, code) => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url)
      } else {
        const textarea = document.createElement('textarea')
        textarea.value = url
        textarea.style.position = 'fixed'
        textarea.style.opacity = '0'
        document.body.appendChild(textarea)
        textarea.select()
        const ok = document.execCommand('copy')
        document.body.removeChild(textarea)
        if (!ok) throw new Error('execCommand failed')
      }
      setCopiedCode(code)
      setTimeout(() => setCopiedCode(null), 2000)
    } catch {
      setNotice('复制失败，请手动复制')
    }
  }

  const toggleAll = (checked) => {
    if (!checked) { setSelected({}); return }
    const next = {}
    users.forEach((user) => { next[user.id] = true })
    setSelected(next)
  }

  const updateUser = async (id, action) => {
    await apiRequest('/admin/users/toggle', { method: 'POST', body: JSON.stringify({ user_id: id, action }) })
    setNotice(`用户已${action === 'ban' ? '禁用' : '启用'}`)
    await loadUsers()
  }

  const openExpiryEditor = (user) => {
    setEditingUser(user)
    setExpiryDate(user.expiry_date || '')
    setNeverExpire(Boolean(user.never_expire))
    setAlertThreshold(user.alert_threshold != null ? String(user.alert_threshold) : '')
  }

  const saveExpiry = async () => {
    if (!editingUser) return
    await apiRequest('/admin/users/expiry', { method: 'POST', body: JSON.stringify({ user_id: editingUser.id, expiry_date: neverExpire ? '' : expiryDate, never_expire: neverExpire }) })
    await apiRequest('/admin/users/alert_threshold', { method: 'POST', body: JSON.stringify({ user_id: editingUser.id, alert_threshold: alertThreshold }) })
    setNotice('设置已更新')
    setEditingUser(null)
    await loadUsers()
  }

  const clearExpiry = async () => {
    if (!editingUser) return
    await apiRequest('/admin/users/expiry', { method: 'POST', body: JSON.stringify({ user_id: editingUser.id, expiry_date: '', never_expire: false }) })
    await apiRequest('/admin/users/alert_threshold', { method: 'POST', body: JSON.stringify({ user_id: editingUser.id, alert_threshold: '' }) })
    setNotice('设置已清除')
    setEditingUser(null)
    await loadUsers()
  }

  const batchAction = async (action) => {
    if (!selectedIds.length) return
    const payload = { user_ids: selectedIds }
    if (action === 'add_days') {
      const days = Number(customDays || 0)
      if (!days) return
      payload.days = days
      await apiRequest('/admin/users/batch_expiry', { method: 'POST', body: JSON.stringify(payload) })
      setCustomDays('')
      setNotice(`已为 ${selectedIds.length} 个用户增加到期天数`)
    } else if (action === 'clear_expiry') {
      await apiRequest('/admin/users/batch_clear_expiry', { method: 'POST', body: JSON.stringify(payload) })
      setNotice(`已清除 ${selectedIds.length} 个用户到期时间`)
    } else if (action === 'never_expire') {
      await apiRequest('/admin/users/batch_never_expire', { method: 'POST', body: JSON.stringify(payload) })
      setNotice(`已设置 ${selectedIds.length} 个用户永不过期`)
    } else if (action === 'ban' || action === 'unban') {
      await apiRequest('/admin/users/batch_toggle', { method: 'POST', body: JSON.stringify({ ...payload, action }) })
      setNotice(`已${action === 'ban' ? '禁用' : '启用'} ${selectedIds.length} 个用户`)
    } else if (action === 'alert_threshold') {
      const threshold = batchThreshold.trim()
      if (!threshold) return
      await apiRequest('/admin/users/batch_alert_threshold', { method: 'POST', body: JSON.stringify({ ...payload, alert_threshold: Number(threshold) }) })
      setBatchThreshold('')
      setNotice(`已为 ${selectedIds.length} 个用户设置告警阈值`)
    } else if (action === 'clear_alert_threshold') {
      await apiRequest('/admin/users/batch_alert_threshold', { method: 'POST', body: JSON.stringify({ ...payload, alert_threshold: '' }) })
      setNotice(`已清除 ${selectedIds.length} 个用户告警阈值`)
    }
    setSelected({})
    await loadUsers()
  }

  return (
    <>
      <Header>
        <h1 className='text-lg font-medium'>用户管理</h1>
      </Header>
      <Main>
        <Tabs defaultValue='system' className='space-y-6'>
          <TabsList>
            <TabsTrigger value='system'>系统面板</TabsTrigger>
            <TabsTrigger value='users'>用户信息</TabsTrigger>
          </TabsList>

          <TabsContent value='system'>
            <div className='space-y-4'>
              {serverInfo && (
                <Card>
                  <CardContent className='p-4'>
                    <div className='flex items-center gap-6 flex-wrap'>
                      <div className='flex items-center gap-3'>
                        <Server className='h-8 w-8 text-primary' />
                        <div>
                          <div className='text-lg font-bold'>{serverInfo.server_name || 'Emby 服务器'}</div>
                          <div className='text-sm text-muted-foreground'>v{serverInfo.version}</div>
                        </div>
                      </div>
                      <div className='h-8 w-px bg-border' />
                      <div className='flex items-center gap-2'>
                        {serverInfo.is_running ? <Circle className='h-3 w-3 fill-green-500 text-green-500' /> : <XCircle className='h-3 w-3 fill-red-500 text-red-500' />}
                        <span className='text-sm'>{serverInfo.is_running ? '运行中' : '未连接'}</span>
                      </div>
                      {serverInfo.operating_system && (
                        <>
                          <div className='h-8 w-px bg-border' />
                          <div className='text-sm text-muted-foreground'>{serverInfo.operating_system}</div>
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              <div className='flex items-center justify-between'>
                <h2 className='text-lg font-semibold'>{sessionCountText}</h2>
                {sessions.length > 0 ? (
                  <Badge variant='secondary' className='text-xs'>{sessions.length} 人</Badge>
                ) : null}
              </div>
              {sessionsLoading ? (
                <div className='text-center py-8 text-sm text-muted-foreground'>加载中...</div>
              ) : sessions.length > 0 ? (
                <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-3'>
                  {sessions.map((session) => (
                    <ActiveSessionCard key={session.session_id} session={session} />
                  ))}
                </div>
              ) : (
                <Card>
                  <CardContent className='py-8 text-center text-sm text-muted-foreground'>暂无正在播放</CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value='users'>
        <div className='grid grid-cols-2 gap-4 md:grid-cols-4 mb-6'>
          <Card><CardHeader className='pb-2'><CardTitle className='text-sm'>用户总数</CardTitle></CardHeader><CardContent className='text-2xl font-bold'>{stats.total}</CardContent></Card>
          <Card><CardHeader className='pb-2'><CardTitle className='text-sm'>禁用用户</CardTitle></CardHeader><CardContent className='text-2xl font-bold text-destructive'>{stats.disabled}</CardContent></Card>
          <Card><CardHeader className='pb-2'><CardTitle className='text-sm'>已到期</CardTitle></CardHeader><CardContent className='text-2xl font-bold'>{stats.expired}</CardContent></Card>
          <Card><CardHeader className='pb-2'><CardTitle className='text-sm'>永不过期</CardTitle></CardHeader><CardContent className='text-2xl font-bold'>{stats.never_expire}</CardContent></Card>
        </div>

        <Card className='mb-6'>
          <CardHeader><CardTitle>批量操作（已选 {selectedIds.length}）</CardTitle></CardHeader>
          <CardContent className='flex flex-wrap items-center gap-2'>
            <Input type='number' min={1} value={customDays} onChange={(e) => setCustomDays(e.target.value)} className='w-24' placeholder='天数' />
            <Button size='sm' onClick={() => batchAction('add_days')}><CalendarPlus className='mr-2 h-4 w-4' /> 增加到期天数</Button>
            <Button size='sm' variant='secondary' onClick={() => batchAction('clear_expiry')}>清除到期</Button>
            <Button size='sm' variant='secondary' onClick={() => batchAction('never_expire')}>永不过期</Button>
            <Button size='sm' variant='destructive' onClick={() => batchAction('ban')}><Lock className='mr-2 h-4 w-4' /> 批量禁用</Button>
            <Button size='sm' onClick={() => batchAction('unban')}><LockOpen className='mr-2 h-4 w-4' /> 批量启用</Button>
            <div className='w-full border-t my-1' />
            <Input type='number' min={1} value={batchThreshold} onChange={(e) => setBatchThreshold(e.target.value)} className='w-28' placeholder='告警阈值' />
            <Button size='sm' onClick={() => batchAction('alert_threshold')}>设置告警阈值</Button>
            <Button size='sm' variant='secondary' onClick={() => batchAction('clear_alert_threshold')}>清除告警阈值</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'>
            <CardTitle>用户列表</CardTitle>
            <div className='flex flex-wrap items-center gap-2'>
              <Button variant='secondary' onClick={() => { setInviteOpen(true); setInviteUrl(''); loadInvites() }}><Link2 className='mr-2 h-4 w-4' /> 邀请</Button>
              <Button onClick={() => setCreateOpen(true)}><UserPlus className='mr-2 h-4 w-4' /> 新建用户</Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading && <p className='text-sm text-muted-foreground'>加载中...</p>}
            {error && <p className='text-sm text-destructive'>{error}</p>}
            {notice && <p className='mb-3 text-sm text-primary'>{notice}</p>}

            <div className='space-y-3 md:hidden'>
              {users.map((user) => {
                const status = getUserStatus(user)
                return (
                  <Card key={`mobile-${user.id}`}>
                    <CardContent className='space-y-2 p-4'>
                      <div className='flex items-start justify-between gap-2'>
                        <button type='button' className='text-left text-primary hover:underline' onClick={() => navigate(`/app/admin/user-playback?username=${encodeURIComponent(user.name)}`)}>
                          <UserIdentity name={user.name} groups={user.groups || []} />
                        </button>
                        <Badge variant={status.variant}>{status.label}</Badge>
                      </div>
                      <div className='text-sm text-muted-foreground'>到期：{user.never_expire ? '永不过期' : user.expiry_date || '未设置'}</div>
                      <div className='text-sm text-muted-foreground'>告警阈值：{user.alert_threshold != null ? user.alert_threshold : `${user.effective_alert_threshold || '默认'} (默认)`}</div>
                      <div className='flex flex-wrap gap-2'>
                        <Button size='sm' variant='outline' onClick={() => openExpiryEditor(user)}>设置到期</Button>
                        {user.is_disabled ? <Button size='sm' onClick={() => updateUser(user.id, 'unban')}>启用</Button> : <Button size='sm' variant='destructive' onClick={() => updateUser(user.id, 'ban')}>禁用</Button>}
                        <Button size='sm' variant='destructive' onClick={async () => { if (!window.confirm(`确定删除用户 ${user.name} 吗？`)) return; try { await apiRequest(`/admin/users/${user.id}`, { method: 'DELETE' }); setNotice(`已删除用户 ${user.name}`); await loadUsers() } catch (err) { setNotice(`删除失败：${err.message}`) } }}>删除</Button>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>

            <div className='hidden overflow-x-auto md:block'>
              <Table className='w-full table-fixed'>
                <TableHeader>
                  <TableRow>
                    <TableHead className='w-12'><Checkbox checked={users.length > 0 && selectedIds.length === users.length} onChange={(e) => toggleAll(e.target.checked)} /></TableHead>
                    <TableHead className='w-[28%]'>用户</TableHead>
                    <TableHead className='w-[14%]'>到期时间</TableHead>
                    <TableHead className='w-[10%]'>状态</TableHead>
                    <TableHead className='w-[12%]'>告警阈值</TableHead>
                    <TableHead className='w-[22%]'>操作</TableHead>
                    <TableHead className='w-[8%] text-right'>删除</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => {
                    const status = getUserStatus(user)
                    const thresholdLabel = user.alert_threshold != null ? String(user.alert_threshold) : (user.effective_alert_threshold != null ? `${user.effective_alert_threshold} (默认)` : '默认')
                    return (
                      <TableRow key={user.id}>
                        <TableCell><Checkbox checked={Boolean(selected[user.id])} onChange={(e) => setSelected((prev) => ({ ...prev, [user.id]: e.target.checked }))} /></TableCell>
                        <TableCell className='align-top'><button type='button' className='block w-full text-left text-primary hover:underline' onClick={() => navigate(`/app/admin/user-playback?username=${encodeURIComponent(user.name)}`)}><UserIdentity name={user.name} groups={user.groups || []} /></button></TableCell>
                        <TableCell className='align-top whitespace-nowrap'>{user.never_expire ? '永不过期' : user.expiry_date || '未设置'}</TableCell>
                        <TableCell className='align-top'><Badge variant={status.variant}>{status.label}</Badge></TableCell>
                        <TableCell className='align-top whitespace-nowrap text-sm'>{thresholdLabel}</TableCell>
                        <TableCell className='align-top'>
                          <div className='flex flex-wrap gap-2'>
                            <Button size='sm' variant='outline' onClick={() => openExpiryEditor(user)}>设置</Button>
                            {user.is_disabled ? <Button size='sm' onClick={() => updateUser(user.id, 'unban')}>启用</Button> : <Button size='sm' variant='destructive' onClick={() => updateUser(user.id, 'ban')}>禁用</Button>}
                          </div>
                        </TableCell>
                        <TableCell className='align-top text-right'><Button size='sm' variant='destructive' onClick={async () => { if (!window.confirm(`确定删除用户 ${user.name} 吗？`)) return; try { await apiRequest(`/admin/users/${user.id}`, { method: 'DELETE' }); setNotice(`已删除用户 ${user.name}`); await loadUsers() } catch (err) { setNotice(`删除失败：${err.message}`) } }}>删除</Button></TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogContent className='sm:max-w-lg'>
            <DialogHeader><DialogTitle>新建用户</DialogTitle><DialogDescription>创建一个新的用户账号</DialogDescription></DialogHeader>
            <div className='grid gap-4 py-4'>
              <div className='grid grid-cols-2 gap-4'>
                <div className='grid gap-2'><Label>用户名</Label><Input value={createUsername} onChange={(e) => setCreateUsername(e.target.value)} /></div>
                <div className='grid gap-2'><Label>密码（可不填，默认=用户名）</Label><Input type='password' value={createPassword} onChange={(e) => setCreatePassword(e.target.value)} /></div>
              </div>
              <div className='grid gap-2'>
                <Label>用户模板（复制该用户的权限/功能）</Label>
                <select className='h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm' value={templateUserId} onChange={(e) => setTemplateUserId(e.target.value)}>
                  <option value=''>不使用模板</option>
                  {users.map((user) => <option key={`tpl-${user.id}`} value={user.id}>{user.name}</option>)}
                </select>
              </div>
              <div className='grid gap-2'>
                <Label>用户组（可多选）</Label>
                <div className='grid gap-2 grid-cols-2'>
                  {allGroups.map((group) => (
                    <label key={`cg-${group.id}`} className='flex items-center gap-2 text-sm'>
                      <input type='checkbox' checked={createGroupIds.includes(group.id)} onChange={(e) => { const checked = e.target.checked; setCreateGroupIds((prev) => (checked ? [...prev, group.id] : prev.filter((x) => x !== group.id))) }} />
                      {group.name}
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant='outline' onClick={() => { setCreateOpen(false); setCreateUsername(''); setCreatePassword(''); setTemplateUserId(''); setCreateGroupIds([]) }}>取消</Button>
              <Button onClick={async () => { try { await apiRequest('/admin/users/create', { method: 'POST', body: JSON.stringify({ username: createUsername, password: createPassword, template_user_id: templateUserId, group_ids: createGroupIds }) }); setNotice('用户创建成功'); setCreateOpen(false); setCreateUsername(''); setCreatePassword(''); setTemplateUserId(''); setCreateGroupIds([]); await loadUsers(); await loadGroups() } catch (err) { setNotice(`创建失败：${err.message}`) } }}>创建</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={inviteOpen} onOpenChange={(open) => { if (!open) { setInviteOpen(false); setInviteEmail('') } }}>
          <DialogContent className='sm:max-w-lg'>
            <DialogHeader><DialogTitle>生成邀请链接</DialogTitle><DialogDescription>创建邀请链接供新用户注册</DialogDescription></DialogHeader>
            <div className='grid gap-4 py-4'>
              <div className='grid grid-cols-2 gap-4'>
                <div className='grid gap-2'><Label>有效时间（小时）</Label><Input type='number' min={1} value={inviteHours} onChange={(e) => setInviteHours(e.target.value)} /></div>
                <div className='grid gap-2'><Label>邀请人数</Label><Input type='number' min={1} value={inviteCount} onChange={(e) => setInviteCount(e.target.value)} /></div>
              </div>
              <div className='grid gap-2'>
                <Label>接收邮箱（可选）</Label>
                <Input type='email' placeholder='填写后将自动发送邀请链接到该邮箱' value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} />
              </div>
              <div className='grid gap-2'>
                <Label>属于用户组</Label>
                <select className='h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm' value={inviteGroupId} onChange={(e) => setInviteGroupId(e.target.value)}>
                  <option value=''>不指定</option>
                  {allGroups.map((group) => <option key={`ig-${group.id}`} value={group.id}>{group.name}</option>)}
                </select>
              </div>
              <div className='grid gap-2'>
                <Label>注册账号到期时间（可选）</Label>
                <Input type='date' value={inviteExpiryDate} onChange={(e) => setInviteExpiryDate(e.target.value)} />
              </div>
              {inviteUrl && (
                <div className='rounded border p-3'><div className='text-sm text-muted-foreground mb-1'>新生成链接</div><div className='break-all font-mono text-sm'>{inviteUrl}</div></div>
              )}
              <div className='rounded border p-3'>
                <div className='text-sm font-medium mb-2'>已发邀请链接</div>
                <div className='max-h-56 space-y-2 overflow-auto'>
                  {inviteList.length ? inviteList.map((invite) => {
                    const exhausted = Number(invite.used_count || 0) >= Number(invite.max_uses || 0)
                    const invalid = exhausted || !invite.is_active
                    return (
                      <div key={invite.code} className='rounded border p-2'>
                        <div className='flex items-start justify-between gap-2'>
                          <div className='flex-1 min-w-0'>
                            <div className={`break-all font-mono text-xs ${invalid ? 'line-through text-muted-foreground' : ''}`}>{invite.invite_url}</div>
                            {invite.target_email && <div className='mt-1 text-xs text-muted-foreground'>发送至：{invite.target_email}</div>}
                          </div>
                          <div className='flex items-center gap-2 shrink-0'>
                            <Button size='sm' variant='outline' onClick={() => handleCopyInvite(invite.invite_url, invite.code)}>{copiedCode === invite.code ? '已复制' : '复制'}</Button>
                            <Button size='sm' variant='destructive' onClick={async () => { try { await apiRequest(`/admin/invites/${invite.code}`, { method: 'DELETE' }); setInviteList((prev) => prev.filter((i) => i.code !== invite.code)); setNotice('邀请已删除') } catch (err) { setNotice(`删除邀请失败：${err.message}`) } }}>删除</Button>
                          </div>
                        </div>
                        <div className='mt-1 text-xs text-muted-foreground'>使用进度：{invite.used_count}/{invite.max_uses}</div>
                      </div>
                    )
                  }) : <div className='text-xs text-muted-foreground'>暂无邀请链接</div>}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant='outline' onClick={() => { setInviteOpen(false); setInviteEmail('') }}>关闭</Button>
              <Button onClick={async () => { try { const data = await apiRequest('/admin/invites', { method: 'POST', body: JSON.stringify({ valid_hours: Number(inviteHours || 24), max_uses: Number(inviteCount || 1), group_id: inviteGroupId, account_expiry_date: inviteExpiryDate, target_email: inviteEmail }) }); setInviteUrl(data.invite_url); await loadInvites(); setNotice(inviteEmail ? '邀请链接已生成并发送邮件' : '邀请链接已生成'); setInviteEmail('') } catch (err) { setNotice(`生成失败：${err.message}`) } }}>生成</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={!!editingUser} onOpenChange={(open) => { if (!open) setEditingUser(null) }}>
          <DialogContent className='sm:max-w-md'>
            <DialogHeader><DialogTitle>用户设置 · {editingUser?.name}</DialogTitle></DialogHeader>
            <div className='grid gap-4 py-4'>
              <label className='flex items-center gap-2 text-sm'><input type='checkbox' checked={neverExpire} onChange={(e) => setNeverExpire(e.target.checked)} /> 永不过期</label>
              <Input type='date' disabled={neverExpire} value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} />
              <div className='grid gap-2'>
                <Label>最大播放IP数（告警阈值）</Label>
                <Input type='number' min={1} value={alertThreshold} onChange={(e) => setAlertThreshold(e.target.value)} placeholder='留空使用全局默认值' />
                <p className='text-xs text-muted-foreground'>同一账号允许在不同IP网段同时播放的最大数量，超过将触发告警/封禁。留空则使用全局设置或用户组设置。</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant='secondary' onClick={clearExpiry}>清除</Button>
              <Button variant='outline' onClick={() => setEditingUser(null)}>取消</Button>
              <Button onClick={saveExpiry}>保存</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
          </TabsContent>
        </Tabs>
      </Main>
    </>
  )
}
