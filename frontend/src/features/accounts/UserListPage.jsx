import { useState, useEffect } from "react"
import { useAuth } from '../../shared/hooks/useAuth'
import { Link } from 'react-router-dom'
import { getUserList } from "./accountsApi"
import {
    AUTHORITY_ADMIN,
    AUTHORITY_SHOP,
    AUTHORITY_WAREHOUSE,
    GENDER_MEN,
    GENDER_WOMEN,
    GENDER_OTHERS,
    GENDER_MEN_DISPLAY,
    GENDER_WOMEN_DISPLAY,
    GENDER_OTHERS_DISPLAY,
} from "../../shared/constants"

export default function UserListPage() {
    const [users, setUsers] = useState(null)
    const [filterOptions, setFilterOptions] = useState({ authorities: [], shops: [], warehouses: [] })
    const [filters, setFilters] = useState({ authority: '', shop: '', warehouse: '' })
    const { userInfo } = useAuth()

    useEffect(() => {
        document.title = 'ユーザー管理 | 在庫管理システム'
        // 選択肢は初回のみ取得
        getUserList({}).then(res => {
            setFilterOptions({
                authorities: res.data.authorities,
                shops: res.data.shops,
                warehouses: res.data.warehouses,
            })
            setUsers(res.data.users)
        })
    }, [])

    useEffect(() => {
        // filtersが変わるたびにユーザー一覧だけ更新
        const activeFilters = Object.fromEntries(
            Object.entries(filters).filter(([, v]) => v !== '')
        )
        getUserList(activeFilters).then(res => setUsers(res.data.users))
    }, [filters])

    const handleFilterChange = (e) => {
        const { name, value } = e.target
        if (name === 'authority') {
            const isAdmin     = value == AUTHORITY_ADMIN
            const isShop      = value == AUTHORITY_SHOP
            const isWarehouse = value == AUTHORITY_WAREHOUSE
            setFilters(prev => ({
                ...prev,
                authority: value,
                shop:      (isAdmin || isWarehouse) ? '' : prev.shop,
                warehouse: (isAdmin || isShop)      ? '' : prev.warehouse,
            }))
        } else {
            setFilters(prev => ({ ...prev, [name]: value }))
        }
    }

    const handleReset = () => {
        setFilters({ authority: '', shop: '', warehouse: '' })
    }

    if (users === null) return <div>読み込み中...</div>

    return (
        <div>
            <div className="d-flex user-list-header">
                <div className="row g-3 mb-3">
                    <div className="col-auto d-flex align-items-center gap-2">
                        {userInfo?.authority === AUTHORITY_ADMIN && (
                            <div>
                                <p className="mb-0">権限</p>
                                <select name="authority" className="form-select" value={filters.authority} onChange={handleFilterChange}>
                                    <option value=""> - </option>
                                    {filterOptions.authorities.map(a => (
                                        <option key={a.id} value={a.id}>{a.authority_name}</option>
                                    ))}
                                </select>
                            </div>
                        )}
                        {(userInfo?.authority === AUTHORITY_ADMIN || userInfo?.authority === AUTHORITY_SHOP) && (
                            <div>
                                <p className="mb-0">所属店舗</p>
                                <select
                                    name="shop"
                                    className="form-select"
                                    value={filters.shop}
                                    onChange={handleFilterChange}
                                    disabled={filters.authority == AUTHORITY_ADMIN || filters.authority == AUTHORITY_WAREHOUSE}
                                >
                                    <option value=""> - </option>
                                    {filterOptions.shops.map(s => (
                                        <option key={s.id} value={s.id}>{s.shop_name}</option>
                                    ))}
                                </select>
                            </div>
                        )}
                        {(userInfo?.authority === AUTHORITY_ADMIN || userInfo?.authority === AUTHORITY_WAREHOUSE) && (
                            <div>
                                <p className="mb-0">所属倉庫</p>
                                <select
                                    name="warehouse"
                                    className="form-select"
                                    value={filters.warehouse}
                                    onChange={handleFilterChange}
                                    disabled={filters.authority == AUTHORITY_ADMIN || filters.authority == AUTHORITY_SHOP}
                                >
                                    <option value=""> - </option>
                                    {filterOptions.warehouses.map(w => (
                                        <option key={w.id} value={w.id}>{w.warehouse_name}</option>
                                    ))}
                                </select>
                            </div>
                        )}
                    </div>
                    <div className="col-auto d-flex align-items-end">
                        <button type="button" className="btn btn-outline-secondary ms-1" onClick={handleReset}>リセット</button>
                    </div>
                </div>

                <Link to="#" className="btn btn-primary mb-5 ms-auto">新規作成</Link>

            </div>
            <table className="table">
                <thead>
                    <tr>
                        <th>ユーザー名</th>
                        <th>性別</th>
                        <th>権限</th>
                        <th>所属</th>
                        {userInfo?.authority === AUTHORITY_ADMIN &&
                        <th>操作</th>
                        }
                    </tr>
                </thead>
                <tbody>
                    {users.length > 0 ? (
                        users.map((user) => (
                            <tr key={user.id}>
                                {/* ユーザー名 */}
                                <td>{user.username}</td>
                                {/* 性別 */}
                                <td>{
                                user.user_gender === GENDER_MEN ? GENDER_MEN_DISPLAY
                                : user.user_gender === GENDER_WOMEN ? GENDER_WOMEN_DISPLAY
                                : user.user_gender === GENDER_OTHERS ? GENDER_OTHERS_DISPLAY
                                : '-'
                                }</td>
                                {/* 権限 */}
                                <td>{user.authority__authority_name}</td>
                                {/* 所属 */}
                                <td>{
                                user.authority_id === AUTHORITY_SHOP ? user.shop__shop_name
                                : user.authority_id === AUTHORITY_WAREHOUSE ? user.warehouse__warehouse_name
                                : '-'
                                }</td>
                                {
                                userInfo?.authority === AUTHORITY_ADMIN &&
                                /* 操作 */
                                <td><Link to="#" className="btn btn-sm btn-outline-primary">編集</Link>
                                </td>}
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colspan="4">ユーザーが存在しません</td>
                        </tr>
                    )}
                </tbody>
            </table>

            {/*
            <!-- ページネーション -->
            {% if page_obj.has_other_pages %}
            <nav aria-label="ページネーション">
                <ul className="pagination justify-content-center mt-3">

                    <!-- 前へ -->
                    {% if page_obj.has_previous %}
                    <li className="page-item">
                        <a className="page-link" href="?page={{ page_obj.previous_page_number }}{{ filter_query }}">前へ</a>
                    </li>
                    {% else %}
                    <li className="page-item disabled">
                        <span className="page-link">前へ</span>
                    </li>
                    {% endif %}

                    <!-- ページ番号 -->
                    {% for num in paginator.page_range %}
                    {% if page_obj.number == num %}
                    <li className="page-item active">
                        <span className="page-link">{{ num }}</span>
                    </li>
                    {% else %}
                    <li className="page-item">
                        <a className="page-link" href="?page={{ num }}{{ filter_query }}">{{ num }}</a>
                    </li>
                    {% endif %}
                    {% endfor %}

                    <!-- 次へ -->
                    {% if page_obj.has_next %}
                    <li className="page-item">
                        <a className="page-link" href="?page={{ page_obj.next_page_number }}{{ filter_query }}">次へ</a>
                    </li>
                    {% else %}
                    <li className="page-item disabled">
                        <span className="page-link">次へ</span>
                    </li>
                    {% endif %}

                </ul>
            </nav>
            */}
        </div>
    )
}