import axios from 'axios'

// 支持通过环境变量配置API地址
// 开发模式：使用 Vite 代理，baseURL 为 /api
// 生产模式：如果设置了 VITE_API_BASE_URL，则使用完整地址
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000,
})

// 请求拦截器 - 添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

// 认证相关
export const authApi = {
  sendCode: (email) => api.post('/auth/send-code', { email }),
  verifyCode: (email, code) => api.post('/auth/verify-code', { email, code }),
  validateToken: () => api.post('/auth/validate-token'),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
}

// 任务相关
export const taskApi = {
  list: () => api.get('/tasks'),
  get: (id) => api.get(`/tasks/${id}`),
  create: (data) => api.post('/tasks', data),
  update: (id, data) => api.put(`/tasks/${id}`, data),
  delete: (id) => api.delete(`/tasks/${id}`),
  toggle: (id) => api.post(`/tasks/${id}/toggle`),
  test: (id) => api.post(`/tasks/${id}/test`, {}, { timeout: 180000 }), // 3分钟超时，因为AI响应可能需要较长时间
  getExecutions: (id, limit = 10) => api.get(`/tasks/${id}/executions`, { params: { limit } }),
}

export default api
