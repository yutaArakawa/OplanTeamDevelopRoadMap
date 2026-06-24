import { AUTHORITY_SHOP, AUTHORITY_WAREHOUSE } from '../../shared/constants'

/**
 * ユーザー名・性別・権限・所属の共通バリデーション
 */
export function validateUserFields({ username, user_gender, authority, shop, warehouse }) {
    const errors = {}
    if (!username?.trim())  errors.username    = 'ユーザー名を入力してください'
    if (!user_gender)       errors.user_gender = '性別を選択してください'
    if (!authority)         errors.authority   = '権限を選択してください'
    if (authority == AUTHORITY_SHOP      && !shop)      errors.shop      = '店舗スタッフには所属店舗が必要です'
    if (authority == AUTHORITY_WAREHOUSE && !warehouse)  errors.warehouse = '倉庫スタッフには所属倉庫が必要です'
    return errors
}

/**
 * パスワードバリデーション
 * @param {string} password1
 * @param {string} password2
 * @param {object} options
 * @param {boolean} options.required - 未入力をエラーにするか（作成時: true、更新時: false）
 * @param {string}  options.key1     - エラーキー（デフォルト: 'password1'）
 * @param {string}  options.key2     - エラーキー（デフォルト: 'password2'）
 */
export function validatePassword(password1, password2, { required = true, key1 = 'password1', key2 = 'password2' } = {}) {
    const errors = {}
    if (!password1) {
        if (required) errors[key1] = 'パスワードを入力してください'
    } else if (password1.length < 8) {
        errors[key1] = 'パスワードは8文字以上で入力してください'
    } else if (password1 !== password2) {
        errors[key2] = 'パスワードが一致しません'
    }
    return errors
}
