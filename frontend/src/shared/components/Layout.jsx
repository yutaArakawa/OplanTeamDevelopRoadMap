import './Layout.css'
import { useAuth } from '../hooks/useAuth'
import { Link, useNavigate } from 'react-router-dom'
import { AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE } from "../constants"
import Sidebar from './Sidebar'
import { logoutApi } from '../../features/auth/authApi'

export default function Layout({ children }) {
    const { userInfo } = useAuth()
    const navigate = useNavigate()

    const handleLogout = async () => {
        await logoutApi()
        navigate('/login')
    }

    return (
        <div>
            <nav className={`navbar navbar-default border ${
                  userInfo?.authority == AUTHORITY_ADMIN ? 'header-admin'
                : userInfo?.authority == AUTHORITY_SHOP ? 'header-shop'
                : userInfo?.authority == AUTHORITY_WAREHOUSE ? 'header-warehouse'
                : 'header-default'
            }`}>
                <div className="container-fluid d-flex">
                    <div className="d-flex align-items-center">
                        {/* ログインしている時サイドバーを読み込む */}
                        {userInfo?.authority !== null && <Sidebar />}
                        <Link to="/" className="navbar-brand ms-3">Python Stock App</Link>
                    </div>

                    {userInfo?.authority !== null && 
                    <div className="d-flex align-items-center">
                        <p className="navbar-text mb-0 me-3">
                            { userInfo?.authority_name }:
                            { userInfo?.authority === AUTHORITY_SHOP && userInfo?.shop }
                            { userInfo?.authority === AUTHORITY_WAREHOUSE && userInfo?.warehouse }
                            { userInfo?.username } さんでログイン中
                        </p>

                        <button onClick={handleLogout} className="btn btn-danger">
                            ログアウト
                        </button>
                    </div>
                    }

                </div>
            </nav>

            <main className="container mt-4">{children}</main>
        </div>
    )
}