
import { useEffect } from "react"
import { AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE } from "../../shared/constants"
import { useAuth } from '../../shared/hooks/useAuth'
import AdminHome from './AdminHome'
import ShopHome from './ShopHome'
import WarehouseHome from './WarehouseHome'

export default function HomePage() {
    const { userInfo } = useAuth()

    useEffect(() => {
        document.title = 'ホーム | 在庫管理システム'
    }, [])

    if (userInfo === null) return <div>読み込み中...</div>

    if (userInfo?.authority === AUTHORITY_ADMIN)     return <AdminHome />
    if (userInfo?.authority === AUTHORITY_SHOP)      return <ShopHome />
    if (userInfo?.authority === AUTHORITY_WAREHOUSE) return <WarehouseHome />
}