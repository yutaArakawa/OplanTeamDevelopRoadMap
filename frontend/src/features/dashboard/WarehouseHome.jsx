import { useState, useEffect } from "react"
import { useAuth } from "../../shared/hooks/useAuth"
import { getDashboard } from "./dashboardApi"

export default function WarehouseHome() {
    const [data, setData] = useState(null)
    const { userInfo } = useAuth()

    useEffect(() => {
        getDashboard().then(res => setData(res.data))
    }, [])

    if (!data) return <div>読み込み中...</div>

    return (
        <div>
            <div className="mb-4">
                <h1 className="h3">ホーム</h1>
            </div>

            {/* サマリーカード */}
            <div className="row g-3 mb-4">
                <div className="col-sm-6">
                    <div className="card shadow-sm">
                        <div className="card-body">
                            <p className="text-muted mb-1">在庫品目数</p>
                            <p className="fs-2 fw-bold mb-0">{data.stock_count}</p>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6">
                    <div className="card shadow-sm">
                        <div className="card-body">
                            <p className="text-muted mb-1">新規受注</p>
                            <p className={`fs-2 fw-bold mb-0 ${data.new_order_count > 0 ? 'text-danger' : ''}`}>
                                {data.new_order_count}
                            </p>
                        </div>
                    </div>
                </div>
                <div className="col-sm-6">
                    <div className="card shadow-sm">
                        <div className="card-body">
                            <p className="text-muted mb-1">準備中</p>
                            <p className="fs-2 fw-bold mb-0">{data.preparing_order_count}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* 倉庫在庫一覧 */}
            <div className="card shadow-sm">
                <div className="card-header fw-bold">
                    倉庫在庫一覧（{userInfo?.warehouse}）
                </div>
                <div className="card-body p-0">
                    <table className="table align-middle mb-0">
                        <thead>
                            <tr>
                                <th>商品名</th>
                                <th className="text-end">在庫数</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.warehouse_stocks.length > 0 ? (
                                data.warehouse_stocks.map((s, index) => (
                                    <tr key={index}>
                                        <td>{s.goods__goods_name}</td>
                                        <td className="text-end">{s.stock}</td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="2" className="text-center text-muted py-4">
                                        在庫データがありません
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
