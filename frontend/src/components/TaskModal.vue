<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <div style="flex: 1; display: flex; align-items: center; gap: 8px;">
          <input
            v-model="form.name"
            type="text"
            class="modal-title-input"
            placeholder="任务名称 *必填"
          />
        </div>
        <button class="modal-close" @click="$emit('close')">&times;</button>
      </div>

      <div class="modal-body">
        <!-- 频率选择 -->
        <div class="form-group">
          <label class="form-label">频率</label>
          <div class="frequency-selector">
            <button
              v-for="freq in frequencies"
              :key="freq.value"
              type="button"
              class="frequency-option"
              :class="{ active: form.frequency === freq.value }"
              @click="form.frequency = freq.value"
            >
              {{ freq.label }}
            </button>
          </div>
        </div>

        <!-- 时间配置 - 根据频率显示不同选项 -->
        <div class="form-group">
          <label class="form-label">开启</label>

          <!-- 一次性任务：日期 + 时间 -->
          <div v-if="form.frequency === 'once'" class="schedule-config">
            <div class="config-row">
              <span class="config-label">时间</span>
              <TimePicker v-model="form.scheduled_time" />
            </div>
            <div class="config-row">
              <span class="config-label">日期</span>
              <div style="margin-left: auto;">
                <VueDatePicker
                  :key="'once-' + form.frequency"
                  v-model="dateValue"
                  :enable-time-picker="false"
                  :formats="{ input: 'yyyy-MM-dd' }"
                  auto-apply
                  :clearable="false"
                  :teleport="true"
                  hide-input-icon
                />
              </div>
            </div>
          </div>

          <!-- 每天：只有时间 -->
          <div v-else-if="form.frequency === 'daily'" class="schedule-config">
            <div class="config-row">
              <span class="config-label">时间</span>
              <TimePicker v-model="form.scheduled_time" />
            </div>
          </div>

          <!-- 每周：星期几 + 时间 -->
          <div v-else-if="form.frequency === 'weekly'" class="schedule-config">
            <div class="config-row">
              <span class="config-label">时间</span>
              <TimePicker v-model="form.scheduled_time" />
            </div>
            <div class="config-row">
              <span class="config-label">星期</span>
              <select v-model="form.day_of_week" class="config-select">
                <option v-for="day in weekDays" :key="day.value" :value="day.value">
                  {{ day.label }}
                </option>
              </select>
            </div>
          </div>

          <!-- 每月：每月几号 + 时间 -->
          <div v-else-if="form.frequency === 'monthly'" class="schedule-config">
            <div class="config-row">
              <span class="config-label">时间</span>
              <TimePicker v-model="form.scheduled_time" />
            </div>
            <div class="config-row">
              <span class="config-label">日期</span>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #666; font-size: 13px;">每月</span>
                <input
                  v-model.number="form.day_of_month"
                  type="number"
                  min="1"
                  max="31"
                  class="config-input number-input"
                />
                <span style="color: #666; font-size: 13px;">日</span>
              </div>
            </div>
          </div>

          <!-- 每年：日期 + 时间 -->
          <div v-else-if="form.frequency === 'yearly'" class="schedule-config">
            <div class="config-row">
              <span class="config-label">时间</span>
              <TimePicker v-model="form.scheduled_time" />
            </div>
            <div class="config-row">
              <span class="config-label">日期</span>
              <div style="margin-left: auto;">
                <VueDatePicker
                  :key="'yearly-' + form.frequency"
                  v-model="dateValue"
                  :enable-time-picker="false"
                  :formats="{ input: 'yyyy-MM-dd' }"
                  auto-apply
                  :clearable="false"
                  :teleport="true"
                  hide-input-icon
                />
              </div>
            </div>
          </div>
        </div>

        <!-- 指令内容 -->
        <div class="form-group">
          <label class="form-label">指令 <span v-if="!form.prompt.trim()" class="required-hint">*必填</span></label>
          <textarea
            v-model="form.prompt"
            class="input"
            rows="6"
            placeholder="在此输入提示词。"
            style="resize: vertical"
          ></textarea>
        </div>

        <!-- 专家模式 -->
        <div class="switch-wrapper">
          <div style="display: flex; align-items: center; gap: 8px">
            <span style="font-size: 16px">💡</span>
            <span>专家模式</span>
          </div>
          <div
            class="switch"
            :class="{ active: form.expert_mode }"
            @click="form.expert_mode = !form.expert_mode"
          ></div>
        </div>
      </div>

      <div class="modal-footer">
        <button
          v-if="isEdit"
          class="btn btn-secondary"
          @click="handleTest"
        >
          🧪 测试
        </button>
        <button class="btn btn-primary" :disabled="!canSubmit" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建任务' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import TimePicker from './TimePicker.vue'
import { VueDatePicker } from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'

const props = defineProps({
  task: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'submit', 'test'])

// 获取浏览器本地时区
const localTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone

const frequencies = [
  { label: '一次', value: 'once' },
  { label: '每天', value: 'daily' },
  { label: '每周', value: 'weekly' },
  { label: '每月', value: 'monthly' },
  { label: '每年', value: 'yearly' },
]

const weekDays = [
  { label: '星期一', value: 'mon' },
  { label: '星期二', value: 'tue' },
  { label: '星期三', value: 'wed' },
  { label: '星期四', value: 'thu' },
  { label: '星期五', value: 'fri' },
  { label: '星期六', value: 'sat' },
  { label: '星期日', value: 'sun' },
]

const today = new Date().toISOString().split('T')[0]

const form = ref({
  name: '',
  frequency: 'daily',
  scheduled_time: '10:30',
  scheduled_date: today,
  day_of_week: 'mon',
  day_of_month: 1,
  prompt: '',
  expert_mode: false,
  timezone: localTimezone,  // 用户本地时区
})

const isEdit = computed(() => !!props.task)

const canSubmit = computed(() => {
  return form.value.name.trim() && form.value.prompt.trim()
})

// 日期值转换：VueDatePicker 使用 Date 对象，表单使用 YYYY-MM-DD 字符串
const dateValue = computed({
  get() {
    if (!form.value.scheduled_date) return new Date()
    return new Date(form.value.scheduled_date)
  },
  set(val) {
    if (val) {
      const year = val.getFullYear()
      const month = String(val.getMonth() + 1).padStart(2, '0')
      const day = String(val.getDate()).padStart(2, '0')
      form.value.scheduled_date = `${year}-${month}-${day}`
    }
  }
})

onMounted(() => {
  if (props.task) {
    form.value = {
      name: props.task.name,
      frequency: props.task.frequency,
      scheduled_time: props.task.scheduled_time,
      scheduled_date: props.task.scheduled_date || today,
      day_of_week: props.task.day_of_week || 'mon',
      day_of_month: props.task.day_of_month || 1,
      prompt: props.task.prompt,
      expert_mode: props.task.expert_mode,
      timezone: props.task.timezone || localTimezone,  // 编辑时使用任务时区，无则使用本地时区
    }
  }
})

function handleSubmit() {
  if (!canSubmit.value) return
  emit('submit', { ...form.value })
}

async function handleTest() {
  if (!props.task) return
  emit('test', props.task.id)
  emit('close')  // 关闭模态框，让父组件显示测试进度
}
</script>

<style scoped>
.schedule-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f9f9f9;
  border-radius: 8px;
}

.config-label {
  color: #666;
  white-space: nowrap;
  flex-shrink: 0;
}

.config-label-small {
  font-size: 13px;
  color: #666;
}

.config-input {
  border: none;
  background: transparent;
  font-size: 14px;
  text-align: right;
  outline: none;
}

.config-select {
  border: none;
  background: transparent;
  font-size: 14px;
  text-align: right;
  outline: none;
  cursor: pointer;
  padding: 4px 8px;
}

.number-input {
  width: 50px;
  text-align: center;
  padding: 4px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: white;
}

.config-hint {
  font-size: 12px;
  color: #999;
  padding-left: 16px;
}

.modal-title-input {
  border: none;
  font-size: 18px;
  font-weight: 600;
  outline: none;
  width: 100%;
  background: transparent;
}

.modal-title-input::placeholder {
  color: #999;
}

.required-hint {
  font-size: 12px;
  color: #e74c3c;
  font-weight: normal;
}
</style>

<style>
/* VueDatePicker 样式覆盖 */
.dp__main {
  margin-left: auto !important;
}

.dp__menu {
  border-radius: 12px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
}
</style>
