import { useEffect, useMemo, useState } from 'react'
import UserIdentity from '@/components/UserIdentity'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiRequest } from '@/types/api'

export default function GroupsPage() {
  const [groups, setGroups] = useState([])
  const [users, setUsers] = useState([])
  const [newGroupName, setNewGroupName] = useState('')
  const [activeGroupId, setActiveGroupId] = useState('')
  const [memberId, setMemberId] = useState('')
  const [selectedMembers, setSelectedMembers] = useState({})
  const [filterText, setFilterText] = useState('')
  const [days, setDays] = useState('30')
  const [groupThreshold, setGroupThreshold] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const activeGroup = useMemo(() => groups.find((g) => g.id === activeGroupId), [groups, activeGroupId])
  const activeMemberIds = activeGroup?.members || []

  const loadAll = async () => {
    try {
      const [groupData, userData] = await Promise.all([apiRequest('/admin/groups'), apiRequest('/admin/users')])
      setGroups(groupData.groups || [])
      setUsers(userData.users || [])
      if (!activeGroupId && groupData.groups?.[0]?.id) setActiveGroupId(groupData.groups[0].id)
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { loadAll() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (activeGroup) {
      setGroupThreshold(activeGroup.alert_threshold != null ? String(activeGroup.alert_threshold) : '')
    }
  }, [activeGroup])

  const createGroup = async () => {
    if (!newGroupName.trim()) return
    await apiRequest('/admin/groups', { method: 'POST', body: JSON.stringify({ name: newGroupName.trim() }) })
    setNotice('用户组创建成功'); setNewGroupName(''); await loadAll()
  }

  const removeGroup = async (groupId) => {
    await apiRequest(`/admin/groups/${groupId}`, { method: 'DELETE' })
    setNotice('用户组已删除'); if (activeGroupId === groupId) setActiveGroupId(''); await loadAll()
  }

  const addMember = async () => {
    if (!activeGroupId || !memberId) return
    await apiRequest(`/admin/groups/${activeGroupId}/members`, { method: 'POST', body: JSON.stringify({ user_id: memberId }) })
    setNotice('成员添加成功'); setMemberId(''); await loadAll()
  }

  const addSelectedMembers = async () => {
    if (!activeGroupId) return
    const ids = Object.entries(selectedMembers).filter(([, v]) => v).map(([id]) => id)
    if (!ids.length) return
    for (const id of ids) { await apiRequest(`/admin/groups/${activeGroupId}/members`, { method: 'POST', body: JSON.stringify({ user_id: id }) }) }
    setNotice(`已批量添加 ${ids.length} 个成员`); setSelectedMembers({}); await loadAll()
  }

  const removeMember = async (userId) => {
    if (!activeGroupId) return
    await apiRequest(`/admin/groups/${activeGroupId}/members/${userId}`, { method: 'DELETE' })
    setNotice('成员已移除'); await loadAll()
  }

  const saveGroupThreshold = async () => {
    if (!activeGroupId) return
    await apiRequest(`/admin/groups/${activeGroupId}/alert_threshold`, { method: 'POST', body: JSON.stringify({ alert_threshold: groupThreshold }) })
    setNotice(groupThreshold ? `用户组告警阈值已设置为 ${groupThreshold}` : '用户组告警阈值已清除')
    await loadAll()
  }

  const doGroupBatch = async (kind) => {
    if (!activeMemberIds.length) return
    if (kind === 'add_days') {
      await apiRequest('/admin/users/batch_expiry', { method: 'POST', body: JSON.stringify({ user_ids: activeMemberIds, days: Number(days || 30) }) })
      setNotice(`已为组成员增加 ${days} 天到期时间`)
    } else if (kind === 'clear_expiry') {
      await apiRequest('/admin/users/batch_clear_expiry', { method: 'POST', body: JSON.stringify({ user_ids: activeMemberIds }) })
      setNotice('已清除组成员到期时间')
    } else if (kind === 'never_expire') {
      await apiRequest('/admin/users/batch_never_expire', { method: 'POST', body: JSON.stringify({ user_ids: activeMemberIds }) })
      setNotice('已设置组成员永不过期')
    } else if (kind === 'ban' || kind === 'unban') {
      await apiRequest('/admin/users/batch_toggle', { method: 'POST', body: JSON.stringify({ user_ids: activeMemberIds, action: kind }) })
      setNotice(`已${kind === 'ban' ? '禁用' : '启用'}组成员`)
    } else if (kind === 'set_threshold') {
      const threshold = groupThreshold.trim()
      if (!threshold) return
      await apiRequest('/admin/users/batch_alert_threshold', { method: 'POST', body: JSON.stringify({ user_ids: activeMemberIds, alert_threshold: Number(threshold) }) })
      setNotice(`已为组成员设置告警阈值为 ${threshold}`)
    } else if (kind === 'clear_threshold') {
      await apiRequest('/admin/users/batch_alert_threshold', { method: 'POST', body: JSON.stringify({ user_ids: activeMemberIds, alert_threshold: '' }) })
      setNotice('已清除组成员告警阈值')
    }
    await loadAll()
  }

  return (
    <>
      <Header><h1 className='text-lg font-medium'>用户组管理</h1></Header>
      <Main>
        {error && <p className='text-sm text-destructive mb-4'>{error}</p>}
        {notice && <p className='text-sm text-primary mb-4'>{notice}</p>}

        <Card className='mb-6'>
          <CardHeader><CardTitle>创建用户组</CardTitle></CardHeader>
          <CardContent className='flex gap-2'>
            <Input placeholder='例如 家庭组' value={newGroupName} onChange={(e) => setNewGroupName(e.target.value)} />
            <Button onClick={createGroup}>创建</Button>
          </CardContent>
        </Card>

        <div className='grid gap-4 md:grid-cols-2'>
          <Card>
            <CardHeader><CardTitle>用户组列表</CardTitle></CardHeader>
            <CardContent className='space-y-2'>
              {groups.map((group) => (
                <div key={group.id} role='button' tabIndex={0} onClick={() => setActiveGroupId(group.id)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setActiveGroupId(group.id) }} className={`flex items-center justify-between rounded border p-3 transition-colors hover:bg-accent/40 ${activeGroupId === group.id ? 'border-primary' : ''}`}>
                  <div className='text-left'>
                    <div className='font-medium'>{group.name}</div>
                    <div className='text-xs text-muted-foreground'>
                      {group.members?.length || 0} 个成员
                      {group.alert_threshold != null ? ` · 告警阈值: ${group.alert_threshold}` : ''}
                    </div>
                  </div>
                  <Button size='sm' variant='destructive' onClick={(e) => { e.stopPropagation(); removeGroup(group.id) }}>删除</Button>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>成员与组批量操作</CardTitle></CardHeader>
            <CardContent className='space-y-3'>
              {!activeGroup ? (
                <p className='text-sm text-muted-foreground'>请选择一个用户组</p>
              ) : (
                <>
                  <div className='grid gap-2 rounded border p-3'>
                    <div className='font-medium'>用户组告警阈值</div>
                    <div className='flex items-center gap-2'>
                      <Input type='number' min={1} value={groupThreshold} onChange={(e) => setGroupThreshold(e.target.value)} placeholder='留空使用全局默认值' className='w-32' />
                      <Button size='sm' onClick={saveGroupThreshold}>保存</Button>
                    </div>
                    <p className='text-xs text-muted-foreground'>设置后，该组内未单独配置告警阈值的用户将使用此值。留空则使用全局默认值。</p>
                  </div>

                  <div className='space-y-2 rounded border p-3'>
                    <div className='flex gap-2'>
                      <select className='h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm' value={memberId} onChange={(e) => setMemberId(e.target.value)}>
                        <option value=''>选择要添加的用户</option>
                        {users.filter((u) => !(activeGroup.members || []).includes(u.id)).map((u) => <option key={u.id} value={u.id}>{u.name}{u.groups?.length ? ` (${u.groups.join(' / ')})` : ''}</option>)}
                      </select>
                      <Button onClick={addMember}>添加</Button>
                    </div>
                    <div className='flex items-center gap-2'>
                      <Input placeholder='批量筛选用户' value={filterText} onChange={(e) => setFilterText(e.target.value)} />
                      <Button variant='secondary' onClick={addSelectedMembers}>批量添加</Button>
                    </div>
                    <div className='max-h-48 space-y-2 overflow-auto rounded border p-2'>
                      {users.filter((u) => !(activeGroup.members || []).includes(u.id)).filter((u) => u.name.toLowerCase().includes(filterText.toLowerCase())).map((u) => (
                        <label key={u.id} className='flex items-center gap-2 text-sm'><input type='checkbox' checked={Boolean(selectedMembers[u.id])} onChange={(e) => setSelectedMembers((prev) => ({ ...prev, [u.id]: e.target.checked }))} /><UserIdentity name={u.name} groups={u.groups || []} /></label>
                      ))}
                      {!users.filter((u) => !(activeGroup.members || []).includes(u.id)).filter((u) => u.name.toLowerCase().includes(filterText.toLowerCase())).length && <p className='text-xs text-muted-foreground'>没有可添加的用户</p>}
                    </div>
                  </div>
                  <div className='grid gap-3 rounded border p-3'>
                    <div className='font-medium'>组内批量操作</div>
                    <div className='flex flex-wrap items-center gap-2'>
                      <Input type='number' className='w-24' value={days} onChange={(e) => setDays(e.target.value)} />
                      <Button size='sm' onClick={() => doGroupBatch('add_days')}>增加到期天数</Button>
                      <Button size='sm' variant='secondary' onClick={() => doGroupBatch('clear_expiry')}>清除到期</Button>
                      <Button size='sm' variant='secondary' onClick={() => doGroupBatch('never_expire')}>永不过期</Button>
                      <Button size='sm' variant='destructive' onClick={() => doGroupBatch('ban')}>禁用组成员</Button>
                      <Button size='sm' onClick={() => doGroupBatch('unban')}>启用组成员</Button>
                    </div>
                    <div className='flex flex-wrap items-center gap-2'>
                      <Input type='number' min={1} className='w-24' value={groupThreshold} onChange={(e) => setGroupThreshold(e.target.value)} placeholder='阈值' />
                      <Button size='sm' onClick={() => doGroupBatch('set_threshold')}>设置组员告警阈值</Button>
                      <Button size='sm' variant='secondary' onClick={() => doGroupBatch('clear_threshold')}>清除组员告警阈值</Button>
                    </div>
                  </div>
                  <div className='rounded border p-3'>
                    <div className='mb-2 font-medium'>当前成员</div>
                    <div className='space-y-2'>
                      {(activeGroup.members || []).length ? activeGroup.members.map((userId) => {
                        const user = users.find((u) => u.id === userId)
                        if (!user) return null
                        const thresholdInfo = user.alert_threshold != null ? `阈值: ${user.alert_threshold}` : (user.effective_alert_threshold != null ? `阈值: ${user.effective_alert_threshold} (默认)` : '')
                        return <div key={userId} className='flex items-center justify-between gap-2 rounded border p-2'><div className='flex-1'><UserIdentity name={user.name} groups={user.groups || []} />{thresholdInfo && <span className='ml-2 text-xs text-muted-foreground'>{thresholdInfo}</span>}</div><Button size='sm' variant='destructive' onClick={() => removeMember(userId)}>移除</Button></div>
                      }) : <p className='text-sm text-muted-foreground'>当前组暂无成员</p>}
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}
