import { useLocation, useNavigate } from 'react-router-dom'
import { SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, useSidebar } from '@/components/ui/sidebar'

export function NavGroup({ title, items }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { setOpenMobile } = useSidebar()
  const href = location.pathname

  return (
    <SidebarGroup>
      <SidebarGroupLabel>{title}</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => {
          const Icon = item.icon
          const isActive = checkIsActive(href, item)
          return (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton asChild isActive={isActive} tooltip={item.title} onClick={() => { navigate(item.url); setOpenMobile(false) }}>
                <span className='cursor-pointer'>
                  {Icon && <Icon />}
                  <span>{item.title}</span>
                </span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          )
        })}
      </SidebarMenu>
    </SidebarGroup>
  )
}

function checkIsActive(href, item) {
  return href === item.url || href.split('?')[0] === item.url
}
