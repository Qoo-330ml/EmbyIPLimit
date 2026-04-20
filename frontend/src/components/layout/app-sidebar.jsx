import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarRail } from '@/components/ui/sidebar'
import { NavGroup } from '@/components/layout/nav-group'
import { NavUser } from '@/components/layout/nav-user'
import { sidebarData } from '@/components/layout/data/sidebar-data'
import { useAuth } from '@/context/AuthContext'

export function AppSidebar(props) {
  const { user } = useAuth()

  const navGroups = (() => {
    if (user?.is_temp_admin) {
      return sidebarData.adminNavGroups
    }
    if (user?.is_admin || user?.is_admin_emby) {
      return [
        ...sidebarData.userNavGroups,
        ...sidebarData.adminNavGroups,
      ]
    }
    return sidebarData.userNavGroups
  })()

  return (
    <Sidebar collapsible='icon' {...props}>
      <SidebarHeader>
        <div className='flex items-center gap-2 px-2 py-1'>
          <img src='/favicon.svg' alt='EmbyQ' className='size-6 shrink-0' style={{ width: 'auto', height: '30px' }} />
          <span className='text-lg font-semibold group-data-[collapsible=icon]:hidden'>EmbyQ</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {navGroups.map((group) => (
          <NavGroup key={group.title} title={group.title} items={group.items} />
        ))}
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
