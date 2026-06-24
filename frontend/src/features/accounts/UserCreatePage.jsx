import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../shared/hooks/useAuth'
import { AUTHORITY_ADMIN, AUTHORITY_SHOP, AUTHORITY_WAREHOUSE } from '../../shared/constants'
import { getUserFormOptions, createUser } from './accountsApi'
import { validateUserFields, validatePassword } from './userValidation'

export default function UserCreatePage() {
    const { userInfo } = useAuth()
    const navigate = useNavigate()

    const [options, setOptions] = useState({ authorities: [], shops: [], warehouses: [] })
    const [form, setForm] = useState({
        username: '',
        password1: '',
        password2: '',
        user_gender: '',
        authority: '',
        shop: '',
        warehouse: '',
    })
    const [errors, setErrors] = useState({})
    const [submitting, setSubmitting] = useState(false)

    useEffect(() => {
        document.title = 'ユーザー作成 | 在庫管理システム'
        getUserFormOptions().then(res => setOptions(res.data))
    }, [])

    const handleChange = (e) => {
        const { name, value } = e.target
        if (name === 'authority') {
            // 権限変更時に所属をリセット
            const isAdmin     = value == AUTHORITY_ADMIN
            const isShop      = value == AUTHORITY_SHOP
            const isWarehouse = value == AUTHORITY_WAREHOUSE
            setForm(prev => ({
                ...prev,
                authority: value,
                shop:      (isAdmin || isWarehouse) ? '' : prev.shop,
                warehouse: (isAdmin || isShop)      ? '' : prev.warehouse,
            }))
        } else {
            setForm(prev => ({ ...prev, [name]: value }))
        }
        setErrors(prev => ({ ...prev, [name]: '' }))
    }

    const validate = () => ({
        ...validateUserFields(form),
        ...validatePassword(form.password1, form.password2, { required: true }),
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
            await createUser(form)
            navigate('/accounts/user/list', { state: { message: 'ユーザーを作成しました。' } })
        } catch (err) {
            if (err.response?.data?.errors) {
                setErrors(err.response.data.errors)
            } else {
                setErrors({ _general: err.response?.data?.error || '作成に失敗しました。もう一度お試しください。' })
            }
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <div>
            <div className="mb-4">
                <h1 className="h3">ユーザー作成</h1>
            </div>

            <div className="row justify-content-center">
                <div className="col-md-5 bg-light py-4 px-4 rounded">
                    {errors._general && (
                        <div className="alert alert-danger">{errors._general}</div>
                    )}
                    {!errors._general && Object.values(errors).some(e => e) && (
                        <div className="alert alert-danger">入力内容に誤りがあります</div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="mb-3">
                            <label className="form-label">ユーザー名</label>
                            <input type="text" name="username" className={`form-control ${errors.username ? 'is-invalid' : ''}`}
                                value={form.username} onChange={handleChange} />
                            {errors.username && <div className="invalid-feedback">{errors.username}</div>}
                        </div>

                        <div className="mb-3">
                            <label className="form-label">パスワード</label>
                            <input type="password" name="password1" className={`form-control ${errors.password1 ? 'is-invalid' : ''}`}
                                value={form.password1} onChange={handleChange} />
                            {errors.password1 && <div className="invalid-feedback">{errors.password1}</div>}
                        </div>

                        <div className="mb-3">
                            <label className="form-label">パスワード確認</label>
                            <input type="password" name="password2" className={`form-control ${errors.password2 ? 'is-invalid' : ''}`}
                                value={form.password2} onChange={handleChange} />
                            {errors.password2 && <div className="invalid-feedback">{errors.password2}</div>}
                        </div>

                        <div className="mb-3">
                            <label className="form-label">性別</label>
                            <select name="user_gender" className={`form-select ${errors.user_gender ? 'is-invalid' : ''}`}
                                value={form.user_gender} onChange={handleChange}>
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
                                value={form.authority} onChange={handleChange}>
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
                            <button type="submit" className="btn btn-primary" disabled={submitting}>作成</button>
                            <Link to="/accounts/user/list" className="btn btn-secondary">戻る</Link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    )
}
