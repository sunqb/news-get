<template>
  <div class="time-picker" ref="picker">
    <div class="time-display" @click="toggleDropdown">
      <span>{{ displayTime }}</span>
    </div>
    <div v-if="isOpen" class="time-dropdown">
      <div class="time-columns">
        <div class="time-column">
          <div
            v-for="h in hours"
            :key="'h' + h"
            class="time-option"
            :class="{ selected: h === selectedHour }"
            @click="selectHour(h)"
          >
            {{ h }}
          </div>
        </div>
        <div class="time-separator">:</div>
        <div class="time-column">
          <div
            v-for="m in minutes"
            :key="'m' + m"
            class="time-option"
            :class="{ selected: m === selectedMinute }"
            @click="selectMinute(m)"
          >
            {{ m }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '10:00'
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const picker = ref(null)

const selectedHour = ref('10')
const selectedMinute = ref('00')

// 生成小时和分钟选项
const hours = computed(() => {
  return Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
})

const minutes = computed(() => {
  return Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'))
})

const displayTime = computed(() => {
  return `${selectedHour.value}:${selectedMinute.value}`
})

// 初始化
watch(() => props.modelValue, (val) => {
  if (val) {
    const [h, m] = val.split(':')
    selectedHour.value = h.padStart(2, '0')
    selectedMinute.value = m.padStart(2, '0')
  }
}, { immediate: true })

function toggleDropdown() {
  isOpen.value = !isOpen.value
}

function selectHour(h) {
  selectedHour.value = h
  emitValue()
}

function selectMinute(m) {
  selectedMinute.value = m
  emitValue()
  isOpen.value = false
}

function emitValue() {
  emit('update:modelValue', `${selectedHour.value}:${selectedMinute.value}`)
}

// 点击外部关闭
function handleClickOutside(e) {
  if (picker.value && !picker.value.contains(e.target)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.time-picker {
  position: relative;
}

.time-display {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 80px;
  padding: 8px 16px;
  font-size: 15px;
  color: #333;
  font-weight: 500;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.time-display:hover {
  border-color: #007AFF;
  background: #f0f7ff;
}

.time-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
}

.time-columns {
  display: flex;
  align-items: stretch;
  padding: 8px;
  gap: 4px;
}

.time-column {
  width: 56px;
  max-height: 200px;
  overflow-y: auto;
  scrollbar-width: thin;
}

.time-column::-webkit-scrollbar {
  width: 4px;
}

.time-column::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 2px;
}

.time-separator {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #666;
  padding: 0 2px;
}

.time-option {
  padding: 8px 12px;
  text-align: center;
  font-size: 14px;
  color: #333;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.time-option:hover {
  background: #f5f5f5;
}

.time-option.selected {
  background: #007AFF;
  color: #fff;
}
</style>
