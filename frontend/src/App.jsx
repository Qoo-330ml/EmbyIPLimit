import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import HomePage from '@/pages/HomePage'
import LoginPage from '@/pages/LoginPage'
import SearchPage from '@/pages/SearchPage'
import AdminPage from '@/pages/AdminPage'
import ConfigPage from '@/pages/ConfigPage'
import GroupsPage from '@/pages/GroupsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path='/' element={<HomePage />} />
        <Route path='/login' element={<LoginPage />} />
        <Route path='/search' element={<SearchPage />} />
        <Route path='/admin' element={<AdminPage />} />
        <Route path='/admin/config' element={<ConfigPage />} />
        <Route path='/admin/groups' element={<GroupsPage />} />
        <Route path='*' element={<Navigate to='/' replace />} />
      </Routes>
    </BrowserRouter>
  )
}
