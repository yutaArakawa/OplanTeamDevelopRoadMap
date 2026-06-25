import { useState, useEffect } from "react"
import { getDashboard } from "./dashboardApi"

export default function ShopHome() {
    const [data, setData] = useState(null)

    useEffect(() => {
        getDashboard().then(res => setData(res.data))
    }, [])

    if (!data) return <div>読み込み中...</div>

    return (
        <div>
            <div className="mb-4">
                <h1 className="h3">ホーム</h1>
            </div>

            <div className="row g-4">
                {/* 自店舗 発注ランキング */}
                <div className="col-md-6">
                    <div className="card shadow-sm h-100">
                        <div className="card-header fw-bold">
                            自店舗 発注ランキング（過去1か月）
                            {data.ranking_date && (
                                <small className="fw-normal text-muted ms-2">
                                    集計日: {data.ranking_date}
                                </small>
                            )}
                        </div>
                        <div className="card-body p-0">
                            <table className="table align-middle mb-0">
                                <thead>
                                    <tr>
                                        <th>順位</th>
                                        <th>商品名</th>
                                        <th className="text-end">発注数</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.shop_ranking.length > 0 ? (
                                        data.shop_ranking.map((item, index) => (
                                            <tr key={index}>
                                                <td>{index + 1}</td>
                                                <td>{item.goods__goods_name}</td>
                                                <td className="text-end">{item.total_quantity_sum}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="3" className="text-center text-muted py-4">
                                                過去1か月の発注データがありません
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* 全店舗 発注ランキング */}
                <div className="col-md-6">
                    <div className="card shadow-sm h-100">
                        <div className="card-header fw-bold">
                            全店舗 発注ランキング（過去1か月）
                        </div>
                        <div className="card-body p-0">
                            <table className="table align-middle mb-0">
                                <thead>
                                    <tr>
                                        <th>順位</th>
                                        <th>商品名</th>
                                        <th className="text-end">発注数</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.all_shop_ranking.length > 0 ? (
                                        data.all_shop_ranking.map((item, index) => (
                                            <tr key={index}>
                                                <td>{index + 1}</td>
                                                <td>{item.goods__goods_name}</td>
                                                <td className="text-end">{item.total_quantity_sum}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="3" className="text-center text-muted py-4">
                                                過去1か月の発注データがありません
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
