import { useState, useEffect } from "react"
import { Link } from 'react-router-dom'
import { getDashboard } from "./dashboardApi"

export default function AdminHome() {
    const[ data, setData] = useState(null)

    useEffect(() => {
        getDashboard().then(res => setData(res.data))
    }, [])

    if (!data) return <div>読み込み中...</div>

    return (
        <div>
            <div className="mb-4">
                <h1 className="h3">ホーム</h1>
            </div>

            <div className="row g-3 mb-4">
                <div className="col-sm-6 col-lg-4">
                    <div className="card shadow-sm h-100">
                        <div className="card-body">
                            <p className="text-muted mb-1">倉庫数</p>
                            <p className="fs-2 fw-bold mb-0">{data.warehouse_count}</p>
                        </div>
                        <div className="card-footer bg-transparent">
                            <Link to="#" className="btn btn-sm btn-outline-primary">倉庫管理へ</Link>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6 col-lg-4">
                    <div className="card shadow-sm h-100">
                        <div className="card-body">
                            <p className="text-muted mb-1">店舗数</p>
                            <p className="fs-2 fw-bold mb-0">{data.shop_count}</p>
                        </div>
                        <div className="card-footer bg-transparent">
                            <Link to="#" className="btn btn-sm btn-outline-primary">店舗管理へ</Link>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6 col-lg-4">
                    <div className="card shadow-sm h-100">
                        <div className="card-body">
                            <p className="text-muted mb-1">商品数</p>
                            <p className="fs-2 fw-bold mb-0">{data.goods_count}</p>
                        </div>
                        <div className="card-footer bg-transparent">
                            <Link to="#" className="btn btn-sm btn-outline-primary">商品管理へ</Link>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6 col-lg-4">
                    <div className="card shadow-sm h-100">
                        <div className="card-body">
                            <p className="text-muted mb-1">ユーザー数</p>
                            <p className="fs-2 fw-bold mb-0">{data.user_count}</p>
                        </div>
                        <div className="card-footer bg-transparent">
                            <Link to="#" className="btn btn-sm btn-outline-primary">ユーザー管理へ</Link>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6 col-lg-4">
                    <div className="card shadow-sm h-100">
                        <div className="card-body">
                            <p className="text-muted mb-1">未処理発注</p>
                            <p className={`fs-2 fw-bold mb-0 ${data.pending_order_count > 0 ? 'text-danger' : ''}`}>
                                {data.pending_order_count}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}