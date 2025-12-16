import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, taskApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  async function sendCode(email) {
    const response = await authApi.sendCode(email)
    return response.data
  }

  async function verifyCode(email, code) {
    const response = await authApi.verifyCode(email, code)
    token.value = response.data.access_token
    localStorage.setItem('token', token.value)
    await fetchUser()
    return response.data
  }

  async function fetchUser() {
    if (!token.value) return null
    try {
      const response = await authApi.getMe()
      user.value = response.data
      return user.value
    } catch (error) {
      logout()
      throw error
    }
  }

  async function validateToken() {
    if (!token.value) return false
    try {
      await authApi.validateToken()
      await fetchUser()
      return true
    } catch (error) {
      logout()
      return false
    }
  }

  function logout() {
    // 尝试调用后端登出
    if (token.value) {
      authApi.logout().catch(() => {})
    }
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isAuthenticated,
    sendCode,
    verifyCode,
    fetchUser,
    validateToken,
    logout,
  }
})

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const loading = ref(false)

  async function fetchTasks() {
    loading.value = true
    try {
      const response = await taskApi.list()
      tasks.value = response.data.tasks
      return tasks.value
    } finally {
      loading.value = false
    }
  }

  async function createTask(data) {
    const response = await taskApi.create(data)
    tasks.value.unshift(response.data)
    return response.data
  }

  async function updateTask(id, data) {
    const response = await taskApi.update(id, data)
    const index = tasks.value.findIndex((t) => t.id === id)
    if (index !== -1) {
      tasks.value[index] = response.data
    }
    return response.data
  }

  async function deleteTask(id) {
    await taskApi.delete(id)
    tasks.value = tasks.value.filter((t) => t.id !== id)
  }

  async function toggleTask(id) {
    const response = await taskApi.toggle(id)
    const index = tasks.value.findIndex((t) => t.id === id)
    if (index !== -1) {
      tasks.value[index] = response.data
    }
    return response.data
  }

  async function testTask(id) {
    const response = await taskApi.test(id)
    return response.data
  }

  return {
    tasks,
    loading,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    toggleTask,
    testTask,
  }
})
