import axios from 'axios'

const apiBase = import.meta.env.VITE_API_BASE || '/api'

function getCookie(name) {
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop().split(';').shift()
    return null
}

const apiClient = axios.create({
  baseURL: apiBase,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Cookie を含める（CSRF 対応）
})

apiClient.interceptors.request.use(config => {
  config.headers['X-CSRFToken'] = getCookie('csrftoken')
  return config
})

// エラーハンドリング
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401 && !window.location.pathname.includes('/login')) {
      // 認証エラー時はログイン画面へ（ログイン画面からのリクエストは除外）
      window.location.href = '/react/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient