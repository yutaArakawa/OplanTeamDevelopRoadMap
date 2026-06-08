import axios from 'axios'

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const apiBase = import.meta.env.VITE_API_BASE || '/api'

const apiClient = axios.create({
  baseURL: apiUrl + apiBase,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Cookie を含める（CSRF 対応）
})

// エラーハンドリング
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 認証エラー時はログイン画面へ
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient