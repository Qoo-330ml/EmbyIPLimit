import { useNavigate } from 'react-router-dom'
import { BadgeCheck, ChevronsUpDown, LogOut, Check, Moon, Sun, Shield, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem, useSidebar } from '@/components/ui/sidebar'
import { useTheme } from '@/context/theme-provider'
import { apiRequest } from '@/types/api'

export function NavUser({ user }) {
  const { isMobile } = useSidebar()
  const navigate = useNavigate()
  const { theme, setTheme } = useTheme()

  const handleLogout = async () => {
    try {
      await apiRequest('/auth/logout', { method: 'POST' })
    } catch { /* ignore */ }
    navigate('/')
  }

  const isEmbyAdmin = user?.is_admin_emby || false
  const isTempAdmin = user?.is_temp_admin || false

  const roleLabel = isTempAdmin ? '临时管理员' : isEmbyAdmin ? 'Emby 管理员' : '用户'

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton size='lg' className='data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground'>
              <Avatar className='h-8 w-8 rounded-lg'>
                <AvatarFallback className='rounded-lg'>{user?.username?.[0]?.toUpperCase() || 'U'}</AvatarFallback>
              </Avatar>
              <div className='grid flex-1 text-start text-sm leading-tight'>
                <div className='flex items-center gap-1.5'>
                  <span className='truncate font-semibold'>{user?.username || ''}</span>
                  {isTempAdmin && <AlertTriangle className='size-3.5 text-yellow-500 shrink-0' />}
                  {isEmbyAdmin && !isTempAdmin && <Shield className='size-3.5 text-blue-500 shrink-0' />}
                </div>
                <span className='truncate text-xs'>{roleLabel}</span>
              </div>
              <ChevronsUpDown className='ms-auto size-4' />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent className='w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg' side={isMobile ? 'bottom' : 'right'} align='end' sideOffset={4}>
            <DropdownMenuLabel className='p-0 font-normal'>
              <div className='flex items-center gap-2 px-1 py-1.5 text-start text-sm'>
                <Avatar className='h-8 w-8 rounded-lg'>
                  <AvatarFallback className='rounded-lg'>{user?.username?.[0]?.toUpperCase() || 'U'}</AvatarFallback>
                </Avatar>
                <div className='grid flex-1 text-start text-sm leading-tight'>
                  <div className='flex items-center gap-1.5'>
                    <span className='truncate font-semibold'>{user?.username || ''}</span>
                    {isTempAdmin && <AlertTriangle className='size-3.5 text-yellow-500 shrink-0' />}
                    {isEmbyAdmin && !isTempAdmin && <Shield className='size-3.5 text-blue-500 shrink-0' />}
                  </div>
                  <span className='truncate text-xs'>{roleLabel}</span>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem onClick={() => setTheme('light')}>
                <Sun className='size-4' />
                浅色
                <Check size={14} className={cn('ms-auto', theme !== 'light' && 'hidden')} />
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setTheme('dark')}>
                <Moon className='size-4' />
                深色
                <Check size={14} className={cn('ms-auto', theme !== 'dark' && 'hidden')} />
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setTheme('system')}>
                <BadgeCheck className='size-4' />
                跟随系统
                <Check size={14} className={cn('ms-auto', theme !== 'system' && 'hidden')} />
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut />
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
