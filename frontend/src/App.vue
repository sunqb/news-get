<template>
  <div id="app">
    <div v-if="loading" class="loading-screen">
      <div class="progress-ring"></div>
      <p>加载中...</p>
    </div>
    <Login v-else-if="!isAuthenticated" @login-success="handleLoginSuccess" />
    <TaskList v-else @logout="handleLogout" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from './stores'
import Login from './components/Login.vue'
import TaskList from './components/TaskList.vue'

const authStore = useAuthStore()
const isAuthenticated = ref(false)
const loading = ref(true)

onMounted(async () => {
  // 检查localStorage中是否有token
  if (authStore.token) {
    // 验证token是否有效
    const isValid = await authStore.validateToken()
    isAuthenticated.value = isValid
  }
  loading.value = false
})

function handleLoginSuccess() {
  isAuthenticated.value = true
}

function handleLogout() {
  isAuthenticated.value = false
}
</script>

<style scoped>
.loading-screen {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #666;
}
</style>
