
import { useState, useEffect } from "react"
import { useNavigate } from 'react-router-dom'
import { AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE } from "../../shared/constants"
import { useAuth} from '../../shared/hooks/useAuth'
import AdminHome from './AdminHome'

export default function HomePage() {
    const navigate = useNavigate()
    const { userInfo } = useAuth() // ログインユーザーの権限を取得

    useEffect(() => {
        document.title = 'ホーム | 在庫管理システム'
    }, [])

    // 権限取得中はローディング表示
    if (userInfo === null) return <div>読み込み中...</div>

    if (userInfo?.authority === AUTHORITY_ADMIN)     return <AdminHome />
    //if (userInfo?.authority === AUTHORITY_SHOP)      return <ShopHome />
    //if (userInfo?.authority === AUTHORITY_WAREHOUSE) return <WarehouseHome />
}