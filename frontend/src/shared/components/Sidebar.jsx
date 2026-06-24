import { useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Link } from 'react-router-dom'
import { AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE } from "../constants"

export default function Sidebar({ children }) {
    const { userInfo } = useAuth() // ログインユーザーの権限を取得

    useEffect(() => {
        const sidebarEl = document.querySelector('#offcanvasSidebar')
        if (!sidebarEl) return

        const sidebar = new bootstrap.Offcanvas(sidebarEl)

        const handleMouseMove = (e) => {
            if (e.clientX <= 20) sidebar.show()
        }
        const handleMouseLeave = () => {
            sidebar.hide()
        }

        document.addEventListener('mousemove', handleMouseMove)
        sidebarEl.addEventListener('mouseleave', handleMouseLeave)

        return () => {
            document.removeEventListener('mousemove', handleMouseMove)
            sidebarEl.removeEventListener('mouseleave', handleMouseLeave)
        }
    }, [])

    return (
        <div className="sidebar">
            <button className="navbar-toggler border-0" type="button"
                    data-bs-toggle="offcanvas"
                    data-bs-target="#offcanvasSidebar"
                    aria-controls="offcanvasSidebar">
                <span className="navbar-toggler-icon"></span>
            </button>

            <div className="offcanvas offcanvas-start offcanvas-sidebar"
                tabIndex="-1"
                id="offcanvasSidebar"
                aria-labelledby="offcanvasSidebarLabel">

                <div className="offcanvas-header py-3">
                    <div className="d-flex align-items-center gap-2">
                        <div className="d-flex align-items-center justify-content-center rounded-2 fs-5 sidebar-brand-icon">📦</div>
                        <div>
                            <div className="text-white fw-bold sidebar-brand-title" id="offcanvasSidebarLabel">在庫管理システム</div>
                            <div className="sidebar-brand-subtitle">Navigation Menu</div>
                        </div>
                    </div>
                    <button type="button" className="btn-close btn-close-white opacity-50"
                            data-bs-dismiss="offcanvas" aria-label="Close"></button>
                </div>

                <div className="offcanvas-body p-3">
                    <nav className="d-flex flex-column gap-1">
                        <Link to="/" className="sidebar-link">
                            <span className="sidebar-icon">🏠</span>ホーム
                        </Link>
                        <Link to="/accounts/user/list" className="sidebar-link">
                            <span className="sidebar-icon">👤</span>ユーザー管理
                        </Link>

                        { userInfo?.authority === AUTHORITY_ADMIN && 
                        <div className="admin-menu">
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">🏪</span>店舗一覧
                            </Link>
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">🏭</span>倉庫管理
                            </Link>
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">📦</span>商品管理
                            </Link>
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">🔗</span>倉庫店舗連携管理
                            </Link>
                        </div>
                        }

                        { userInfo?.authority === AUTHORITY_SHOP && 
                        <div className="shop-menu">
                            <div className="sidebar-section-label">在庫・発注</div>
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">📊</span>店舗在庫管理
                            </Link>
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">🔗</span>連携倉庫一覧
                            </Link>
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">🛒</span>商品発注
                            </Link>
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">📋</span>発注履歴
                            </Link>
                        </div>
                        }

                        { userInfo?.authority === AUTHORITY_WAREHOUSE && 
                        <div className="warehouse-menu">
                            <div className="sidebar-section-label">在庫・受注</div>
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">📊</span>倉庫在庫管理
                            </Link>
                            <Link to="#" className="sidebar-link">
                                <span className="sidebar-icon">📥</span>受注管理
                            </Link>
                        </div>
                        }

                        <hr className="sidebar-divider mt-2 mb-1"/>
                        <Link to="#" className="sidebar-link">
                            <span className="sidebar-icon">💬</span>問い合わせ
                        </Link>
                    </nav>
                </div>
            </div>
        </div>
    )
}