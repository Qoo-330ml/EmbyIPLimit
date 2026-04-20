import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from '@/context/theme-provider'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import AppShell from '@/components/AppShell'
import LandingPage from '@/pages/LandingPage'
import LoginPage from '@/pages/LoginPage'
import UserProfilePage from '@/pages/UserProfilePage'
import UserPasswordPage from '@/pages/UserPasswordPage'
import UserPlaybackPage from '@/pages/UserPlaybackPage'
import UserRequestsPage from '@/pages/UserRequestsPage'
import SearchPage from '@/pages/SearchPage'
import AdminPage from '@/pages/AdminPage'
import AdminWishesPage from '@/pages/AdminWishesPage'
import AdminUserPlaybackPage from '@/pages/AdminUserPlaybackPage'
import ConfigPage from '@/pages/ConfigPage'
import GroupsPage from '@/pages/GroupsPage'
import InviteRegisterPage from '@/pages/InviteRegisterPage'
import AboutPage from '@/pages/AboutPage'
import LogPage from '@/pages/LogPage'

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ThemeProvider defaultTheme='system' storageKey='emby-ui-theme'>
          <Routes>
          <Route path='/' element={<LandingPage />} />
          <Route path='/login' element={<LoginPage />} />
          <Route path='/invite/:code' element={<InviteRegisterPage />} />
          <Route path='/app' element={<AppShell />}>
            <Route index element={<Navigate to='/app/user/profile' replace />} />
            <Route path='user/profile' element={<UserProfilePage />} />
            <Route path='user/password' element={<UserPasswordPage />} />
            <Route path='user/playback' element={<UserPlaybackPage />} />
            <Route path='user/requests' element={<UserRequestsPage />} />
            <Route path='search' element={<SearchPage />} />
            <Route path='about' element={<AboutPage />} />
            <Route path='admin' element={<Navigate to='/app/admin/users' replace />} />
            <Route path='admin/users' element={<AdminPage />} />
            <Route path='admin/user-playback' element={<AdminUserPlaybackPage />} />
            <Route path='admin/wishes' element={<AdminWishesPage />} />
            <Route path='admin/config' element={<ConfigPage />} />
            <Route path='admin/groups' element={<GroupsPage />} />
            <Route path='admin/logs' element={<LogPage />} />
          </Route>
          <Route path='*' element={<Navigate to='/' replace />} />
          </Routes>
      </ThemeProvider>
    </BrowserRouter>
    </ErrorBoundary>
  )
}
