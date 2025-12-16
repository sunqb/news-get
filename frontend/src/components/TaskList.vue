<template>
  <div class="container">
    <!-- Toast 组件 -->
    <Toast />

    <!-- 测试进度遮罩 -->
    <div v-if="testingTaskId" class="testing-overlay">
      <div class="testing-content">
        <div class="progress-ring"></div>
        <p>正在执行任务测试...</p>
        <p class="testing-hint">结果将发送到您的邮箱</p>
      </div>
    </div>

    <!-- 页头 -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
      <h1 style="font-size: 24px; font-weight: 600">任务</h1>
      <button class="btn btn-secondary" @click="showCreateModal = true">
        + 创建任务
      </button>
    </div>

    <!-- 任务列表 -->
    <div v-if="loading" class="empty-state">
      <div class="progress-ring"></div>
      <p style="margin-top: 16px">加载中...</p>
    </div>

    <div v-else-if="tasks.length === 0" class="empty-state">
      <div class="empty-state-icon">📋</div>
      <p class="empty-state-text">暂无任务，点击上方按钮创建</p>
    </div>

    <div v-else class="task-list">
      <div v-for="task in tasks" :key="task.id" class="task-item">
        <div class="task-info">
          <div class="task-name">{{ task.name }}</div>
          <div class="task-result">
            <span>🔍</span>
            <span>{{ task.last_result ? truncate(task.last_result, 50) : '暂无执行结果' }}</span>
          </div>
          <div class="task-time">
            {{ formatTime(task.last_run || task.created_at) }}
          </div>
        </div>
        <div class="task-actions">
          <button class="icon-btn" @click="editTask(task)" title="编辑">
            ✏️
          </button>
          <button
            class="icon-btn"
            @click="toggleTask(task)"
            :title="task.is_active ? '暂停' : '启用'"
          >
            {{ task.is_active ? '⏸️' : '▶️' }}
          </button>
          <button class="icon-btn" @click="confirmDelete(task)" title="删除">
            🗑️
          </button>
        </div>
      </div>
    </div>

    <!-- 底部进度指示 -->
    <div v-if="activeTasks.length > 0" class="progress-indicator">
      <div class="progress-ring" style="width: 32px; height: 32px; border-width: 2px"></div>
      <div style="flex: 1">
        <div style="font-weight: 500">{{ activeTasks.length }}个任务进行中</div>
        <div style="font-size: 12px; color: #666">
          共 {{ tasks.length }} 个任务
        </div>
      </div>
      <div v-if="nextRunTime" style="text-align: right; font-size: 12px; color: #666">
        <div>下一次执行时间</div>
        <div style="font-weight: 500; color: #333">{{ formatNextRun(nextRunTime) }}</div>
      </div>
    </div>

    <!-- 用户信息 -->
    <div style="margin-top: 24px; text-align: center; color: #999; font-size: 13px">
      {{ user?.email }}
      <button
        style="margin-left: 12px; color: #666; background: none; border: none; cursor: pointer; text-decoration: underline"
        @click="handleLogout"
      >
        退出登录
      </button>
    </div>

    <!-- 创建/编辑任务模态框 -->
    <TaskModal
      v-if="showCreateModal"
      :task="editingTask"
      @close="closeModal"
      @submit="handleSubmit"
      @test="handleTest"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore, useTaskStore } from '../stores'
import { useToast } from '../composables/useToast'
import TaskModal from './TaskModal.vue'
import Toast from './Toast.vue'

const emit = defineEmits(['logout'])

const authStore = useAuthStore()
const taskStore = useTaskStore()
const toast = useToast()

const showCreateModal = ref(false)
const editingTask = ref(null)
const testingTaskId = ref(null)

const tasks = computed(() => taskStore.tasks)
const loading = computed(() => taskStore.loading)
const user = computed(() => authStore.user)

const activeTasks = computed(() => tasks.value.filter(t => t.is_active))

// 计算最近的下次执行时间
const nextRunTime = computed(() => {
  const activeWithNextRun = activeTasks.value.filter(t => t.next_run)
  if (activeWithNextRun.length === 0) return null

  // 找到最近的执行时间
  const sorted = [...activeWithNextRun].sort((a, b) =>
    new Date(a.next_run) - new Date(b.next_run)
  )
  return sorted[0].next_run
})

onMounted(async () => {
  await taskStore.fetchTasks()
})

function truncate(text, length) {
  if (!text) return ''
  const firstLine = text.split('\n')[0]
  if (firstLine.length <= length) return firstLine
  return firstLine.slice(0, length) + '...'
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`

  return date.toLocaleDateString('zh-CN')
}

function formatNextRun(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = date - now  // 注意：这是未来时间，所以是 date - now

  if (diff < 0) return '即将执行'
  if (diff < 60000) return '不到1分钟后'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟后`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时后`

  // 超过24小时显示具体日期时间
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function editTask(task) {
  editingTask.value = task
  showCreateModal.value = true
}

function closeModal() {
  showCreateModal.value = false
  editingTask.value = null
}

async function handleSubmit(formData) {
  try {
    if (editingTask.value) {
      await taskStore.updateTask(editingTask.value.id, formData)
    } else {
      await taskStore.createTask(formData)
    }
    closeModal()
  } catch (error) {
    alert(error.response?.data?.detail || '操作失败')
  }
}

async function toggleTask(task) {
  try {
    await taskStore.toggleTask(task.id)
  } catch (error) {
    alert(error.response?.data?.detail || '操作失败')
  }
}

async function confirmDelete(task) {
  if (!confirm(`确定要删除任务「${task.name}」吗？`)) return
  try {
    await taskStore.deleteTask(task.id)
  } catch (error) {
    alert(error.response?.data?.detail || '删除失败')
  }
}

async function handleTest(taskId) {
  testingTaskId.value = taskId
  try {
    const result = await taskStore.testTask(taskId)
    toast.success(result.message || '测试任务已完成，结果已发送到邮箱')
    await taskStore.fetchTasks()
  } catch (error) {
    toast.error(error.response?.data?.detail || '测试失败')
  } finally {
    testingTaskId.value = null
  }
}

function handleLogout() {
  authStore.logout()
  emit('logout')
}
</script>
