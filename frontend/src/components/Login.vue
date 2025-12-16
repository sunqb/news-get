<template>
  <div class="login-page">
    <div class="card login-card">
      <h1 class="login-title">News Task Manager</h1>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">邮箱</label>
          <input
            v-model="email"
            type="email"
            class="input"
            placeholder="请输入邮箱地址"
            :disabled="step === 'verify'"
            required
          />
        </div>

        <div v-if="step === 'verify'" class="form-group">
          <label class="form-label">验证码</label>
          <div class="code-input-wrapper">
            <input
              v-model="code"
              type="text"
              class="input"
              placeholder="请输入6位验证码"
              maxlength="6"
              required
            />
            <button
              type="button"
              class="btn btn-secondary send-code-btn"
              :disabled="countdown > 0"
              @click="resendCode"
            >
              {{ countdown > 0 ? `${countdown}s` : '重新发送' }}
            </button>
          </div>
        </div>

        <button
          type="submit"
          class="btn btn-primary"
          style="width: 100%"
          :disabled="loading"
        >
          {{ loading ? '处理中...' : (step === 'email' ? '发送验证码' : '登录') }}
        </button>
      </form>

      <div v-if="step === 'verify'" style="margin-top: 16px; text-align: center">
        <button
          class="btn btn-secondary"
          style="font-size: 13px"
          @click="backToEmail"
        >
          更换邮箱
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores'

const emit = defineEmits(['login-success'])

const authStore = useAuthStore()

const step = ref('email') // 'email' | 'verify'
const email = ref('')
const code = ref('')
const loading = ref(false)
const countdown = ref(0)

let countdownTimer = null

async function handleSubmit() {
  if (loading.value) return

  loading.value = true
  try {
    if (step.value === 'email') {
      await authStore.sendCode(email.value)
      step.value = 'verify'
      startCountdown()
    } else {
      await authStore.verifyCode(email.value, code.value)
      emit('login-success')
    }
  } catch (error) {
    const message = error.response?.data?.detail || '操作失败，请重试'
    alert(message)
  } finally {
    loading.value = false
  }
}

async function resendCode() {
  if (countdown.value > 0) return

  loading.value = true
  try {
    await authStore.sendCode(email.value)
    startCountdown()
  } catch (error) {
    const message = error.response?.data?.detail || '发送失败，请重试'
    alert(message)
  } finally {
    loading.value = false
  }
}

function startCountdown() {
  countdown.value = 60
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
    }
  }, 1000)
}

function backToEmail() {
  step.value = 'email'
  code.value = ''
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdown.value = 0
  }
}
</script>
