import './LoginPage.css'
import {loginApi } from './authApi'
import apiClient from '../../shared/api/client'
import { useState, useEffect } from "react"
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const navigate = useNavigate()

    useEffect(() => {
        document.title = 'ログイン | 在庫管理システム'
        // CSRFトークンを事前取得
        apiClient.get('/auth/csrf/')
    }, [])

    const handleSubmit = async (e) => {
        e.preventDefault() // フォームのデフォルト送信を止める

        if (!username || !password) {
            setError('ユーザー名とパスワードを入力してください')
            return
        }
        try {
            await loginApi(username, password)
            // 成功後ホームへ遷移
            navigate('/')
        } catch (e) {
            //　Django側のエラーメッセージをそのまま表示
            // 認証失敗・削除済み・不正リクエストなど
            setError(e.response?.data?.error || 'ログインに失敗しました')
        }

    }
    return (
        <div className="d-flex align-items-center justify-content-center min-vh-100 login-bg">

            <div className="row justify-content-center w-100 mx-0">
                <div className="col-11 col-sm-8 col-md-6 col-lg-5 col-xl-4">

                    {/* ヘッダー */}
                    <div className="text-center mb-4 text-white">
                        <div className="d-inline-flex align-items-center justify-content-center
                                    rounded-3 p-3 mb-3 fs-3
                                    bg-white bg-opacity-10
                                    border border-white border-opacity-25">
                            📦
                        </div>
                        <h1 className="h5 fw-bold mb-1">在庫管理システム</h1>
                        <p className="small text-white-50 mb-0">倉庫・店舗の在庫を一元管理</p>
                    </div>

                    {/* ログインカード */}
                    <div className="bg-white rounded-4 p-4 shadow-lg">
                        <form onSubmit={handleSubmit}>

                            <div>
                                {/* エラーメッセージ */}
                                {error && (
                                    <div className="alert alert-danger py-2 mb-3" role="alert">
                                        {error}
                                    </div>
                                )}
                            </div>

                            <div className="mb-3">
                                <label htmlFor="username" className="form-label fw-semibold">
                                    ユーザー名
                                </label>
                                <input
                                    type="text"
                                    id="username"
                                    className={`form-control ${error ? 'is-invalid' : ''}`}
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    autofocus
                                    autocomplete="username"
                                />
                            </div>
                            <div className="mb-4">
                                <label htmlFor="password" className="form-label fw-semibold">
                                    パスワード
                                </label>
                                <input
                                    type="password"
                                    id="password"
                                    className={`form-control ${error ? 'is-invalid' : ''}`}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    autocomplete="current-password"
                                />
                            </div>

                            <button type="submit" className="btn btn-dark w-100 fw-semibold">
                                ログイン
                            </button>
                        </form>
                    </div>

                    {/* フッター */}
                    {/*
                    <div className="text-center mt-4">
                        <a href="{% url 'inquiry_create_guest' %}" className="btn btn-outline-light btn-sm">
                            お問い合わせはこちら
                        </a>
                    </div>
                    */}
                </div>
            </div>
            {/* <a href="{% url 'prison' %}" className="prison-link">prison</a> */}

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/js/bootstrap.bundle.min.js"></script>
        </div>
    )
}