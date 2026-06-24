import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom'
import LoginPage from './features/auth/LoginPage'
import HomePage from './features/dashboard/HomePage'
import UserListPage from './features/accounts/UserListPage'
import UserCreatePage from './features/accounts/UserCreatePage'
import UserEditPage from './features/accounts/UserEditPage'
import Layout from './shared/components/Layout'

function App() {
  return (
    <BrowserRouter basename="/react">
      <Routes>

        {/* ログイン画面 */}
        <Route path="/login" element={<LoginPage />} />

        {/* 以降はヘッダーとサイドバーを使用する画面 */}
        <Route element={<Layout><Outlet /></Layout>}>
          {/* ホーム画面 */}
          <Route path="/" element={<HomePage />} />
          {/* ユーザー管理画面 */}
          <Route path="/accounts/user/list" element={<UserListPage />} />
          <Route path="/accounts/user/create" element={<UserCreatePage />} />
          <Route path="/accounts/user/:pk/edit" element={<UserEditPage />} />
        </Route>

      </Routes>
    </BrowserRouter>
  )
}

export default App