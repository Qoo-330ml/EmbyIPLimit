import { FileText, Heart, Info, Key, Play, Settings, Users, UserCircle, FolderTree } from 'lucide-react'

export const sidebarData = {
  adminNavGroups: [
    {
      title: '管理',
      items: [
        { title: '用户管理', url: '/app/admin/users', icon: Users },
        { title: '用户组', url: '/app/admin/groups', icon: FolderTree },
        { title: '求片管理', url: '/app/admin/wishes', icon: Heart },
        { title: '配置', url: '/app/admin/config', icon: Settings },
        { title: '日志', url: '/app/admin/logs', icon: FileText },
      ],
    },
    {
      title: '其他',
      items: [
        { title: '关于', url: '/app/about', icon: Info },
      ],
    },
  ],
  userNavGroups: [
    {
      title: '个人',
      items: [
        { title: '个人信息', url: '/app/user/profile', icon: UserCircle },
        { title: '媒体请求', url: '/app/user/requests', icon: Heart },
        { title: '播放记录', url: '/app/user/playback', icon: Play },
        { title: '修改信息', url: '/app/user/password', icon: Key },
      ],
    },
  ],
}
