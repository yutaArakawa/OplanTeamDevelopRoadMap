import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom'
import LoginPage from './features/auth/LoginPage'
import HomePage from './features/dashboard/HomePage'
import UserListPage from './features/accounts/UserListPage'
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
        </Route>

      </Routes>
    </BrowserRouter>
  )
}

export default App