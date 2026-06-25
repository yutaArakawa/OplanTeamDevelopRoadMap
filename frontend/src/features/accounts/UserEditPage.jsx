import { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useAuth } from '../../shared/hooks/useAuth'
import { AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE } from '../../shared/constants'
import { getUserDetail, updateUser, deleteUser } from './accountsApi'
import { validateUserFields, validatePassword } from './userValidation'

export default function UserEditPage() {
    const { pk } = useParams()
    const { userInfo } = useAuth()
    const navigate = useNavigate()

    const [options, setOptions] = useState({ authorities: [], shops: [], warehouses: [] })
    const [form, setForm] = useState({
        username: '',
        new_password1: '',
        new_password2: '',
        user_gender: '',
        authority: '',
        shop: '',
        warehouse: '',
    })
    const [errors, setErrors] = useState({})
    const [submitting, setSubmitting] = useState(false)
    const [showDeleteModal, setShowDeleteModal] = useState(false)

    const isAdmin = userInfo?.authority === AUTHORITY_ADMIN

    useEffect(() => {
        document.title = 'ユーザー編集 | 在庫管理システム'
        getUserDetail(pk).then(res => {
            const u = res.data.user
            setForm({
                username:      u.username,
                new_password1: '',
                new_password2: '',
                user_gender:   u.user_gender ?? '',
                authority:     u.authority   ?? '',
                shop:          u.shop        ?? '',
                warehouse:     u.warehouse   ?? '',
            })
            setOptions({
                authorities: res.data.authorities,
                shops:       res.data.shops,
                warehouses:  res.data.warehouses,
            })
        })
    }, [pk])

    const handleChange = (e) => {
        const { name, value } = e.target
        if (name === 'authority') {
            const isAdminVal     = value == AUTHORITY_ADMIN
            const isShopVal      = value == AUTHORITY_SHOP
            const isWarehouseVal = value == AUTHORITY_WAREHOUSE
            setForm(prev => ({
                ...prev,
                authority: value,
                shop:      (isAdminVal || isWarehouseVal) ? '' : prev.shop,
                warehouse: (isAdminVal || isShopVal)      ? '' : prev.warehouse,
            }))
        } else {
            setForm(prev => ({ ...prev, [name]: value }))
        }
        setErrors(prev => ({ ...prev, [name]: '' }))
    }

    const validate = () => ({
        ...(isAdmin ? validateUserFields(form) : {}),
        ...validatePassword(form.new_password1, form.new_password2, {
            required: false,
            key1: 'new_password1',
            key2: 'new_password2',
        }),
    })

    const handleSubmit = async (e) => {
        e.preventDefault()
        const errs = validate()
        if (Object.keys(errs).length > 0) {
            setErrors(errs)
            return
        }
        setSubmitting(true)
        try {
            await updateUser(pk, form)
            navigate('/accounts/user/list', { state: { message: 'ユーザー情報を更新しました。' } })
        } catch (err) {
            if (err.response?.data?.errors) {
                setErrors(err.response.data.errors)
            }
        } finally {
            setSubmitting(false)
        }
    }

    const handleDelete = async () => {
        try {
            await deleteUser(pk)
            navigate('/accounts/user/list', { state: { message: 'ユーザーを削除しました。' } })
        } catch (err) {
            setShowDeleteModal(false)
        }
    }

    return (
        <div>
            <div className="mb-4">
                <h1 className="h3">ユーザー編集</h1>
            </div>

            <div className="row justify-content-center">
                <div className="col-md-5 bg-light py-4 px-4 rounded">
                    {Object.values(errors).some(e => e) && (
                        <div className="alert alert-danger">入力内容に誤りがあります</div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="mb-3">
                            <label className="form-label">ユーザー名</label>
                            <input type="text" name="username" className={`form-control ${errors.username ? 'is-invalid' : ''}`}
                                value={form.username} onChange={handleChange} disabled={!isAdmin} />
                            {errors.username && <div className="invalid-feedback">{errors.username}</div>}
                        </div>

                        <div className="mb-3">
                            <label className="form-label">パスワード（変更する場合のみ入力）</label>
                            <input type="password" name="new_password1" className={`form-control ${errors.new_password1 ? 'is-invalid' : ''}`}
                                value={form.new_password1} onChange={handleChange} disabled={!isAdmin} />
                            {errors.new_password1 && <div className="invalid-feedback">{errors.new_password1}</div>}
                        </div>

                        <div className="mb-3">
                            <label className="form-label">パスワード確認</label>
                            <input type="password" name="new_password2" className={`form-control ${errors.new_password2 ? 'is-invalid' : ''}`}
                                value={form.new_password2} onChange={handleChange} disabled={!isAdmin} />
                            {errors.new_password2 && <div className="invalid-feedback">{errors.new_password2}</div>}
                        </div>

                        <div className="mb-3">
                            <label className="form-label">性別</label>
                            <select name="user_gender" className={`form-select ${errors.user_gender ? 'is-invalid' : ''}`}
                                value={form.user_gender} onChange={handleChange} disabled={!isAdmin}>
                                <option value="">---------</option>
                                <option value="1">男</option>
                                <option value="2">女</option>
                                <option value="3">その他</option>
                            </select>
                            {errors.user_gender && <div className="invalid-feedback">{errors.user_gender}</div>}
                        </div>

                        <div className="mb-3">
                            <label className="form-label">権限</label>
                            <select name="authority" className={`form-select ${errors.authority ? 'is-invalid' : ''}`}
                                value={form.authority} onChange={handleChange} disabled={!isAdmin}>
                                <option value="">---------</option>
                                {options.authorities.map(a => (
                                    <option key={a.id} value={a.id}>{a.authority_name}</option>
                                ))}
                            </select>
                            {errors.authority && <div className="invalid-feedback">{errors.authority}</div>}
                        </div>

                        {(userInfo?.authority === AUTHORITY_ADMIN || userInfo?.authority === AUTHORITY_SHOP) && (
                            <div className="mb-3">
                                <label className="form-label">所属店舗</label>
                                <select name="shop" className={`form-select ${errors.shop ? 'is-invalid' : ''}`}
                                    value={form.shop} onChange={handleChange}
                                    disabled={form.authority == AUTHORITY_ADMIN || form.authority == AUTHORITY_WAREHOUSE}>
                                    <option value="">---------</option>
                                    {options.shops.map(s => (
                                        <option key={s.id} value={s.id}>{s.shop_name}</option>
                                    ))}
                                </select>
                                {errors.shop && <div className="invalid-feedback">{errors.shop}</div>}
                            </div>
                        )}

                        {(userInfo?.authority === AUTHORITY_ADMIN || userInfo?.authority === AUTHORITY_WAREHOUSE) && (
                            <div className="mb-3">
                                <label className="form-label">所属倉庫</label>
                                <select name="warehouse" className={`form-select ${errors.warehouse ? 'is-invalid' : ''}`}
                                    value={form.warehouse} onChange={handleChange}
                                    disabled={form.authority == AUTHORITY_ADMIN || form.authority == AUTHORITY_SHOP}>
                                    <option value="">---------</option>
                                    {options.warehouses.map(w => (
                                        <option key={w.id} value={w.id}>{w.warehouse_name}</option>
                                    ))}
                                </select>
                                {errors.warehouse && <div className="invalid-feedback">{errors.warehouse}</div>}
                            </div>
                        )}

                        <div className="d-flex gap-2 mt-4">
                            <button type="submit" className="btn btn-primary" disabled={submitting}>更新</button>
                            <Link to="/accounts/user/list" className="btn btn-secondary">戻る</Link>
                            {isAdmin && (
                                <button type="button" className="btn btn-danger ms-auto"
                                    onClick={() => setShowDeleteModal(true)}>
                                    削除
                                </button>
                            )}
                        </div>
                    </form>
                </div>
            </div>

            {/* 削除確認モーダル */}
            {showDeleteModal && (
                <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">ユーザー削除確認</h5>
                                <button type="button" className="btn-close"
                                    onClick={() => setShowDeleteModal(false)} />
                            </div>
                            <div className="modal-body">本当に削除しますか？</div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary"
                                    onClick={() => setShowDeleteModal(false)}>
                                    キャンセル
                                </button>
                                <button type="button" className="btn btn-danger" onClick={handleDelete}>
                                    削除する
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
