<script setup>
/**
 * SettingsInput — 文本输入设置行
 *
 * 基于 SettingsItem，右侧渲染文本输入框，支持 v-model。
 *
 * Props:
 *   icon        — Material Symbols 图标名称
 *   label       — 主标签文字
 *   description — 副标签文字（可选）
 *   divider     — 是否显示行底分隔线
 *   modelValue  — 输入值（v-model）
 *   placeholder — 输入框占位文字
 *   type        — 输入框类型（text, url, number等）
 */
import SettingsItem from './SettingsItem.vue'

defineProps({
  icon: { type: String, required: true },
  label: { type: String, required: true },
  description: { type: String, default: null },
  divider: { type: Boolean, default: false },
  modelValue: { type: String, required: true },
  placeholder: { type: String, default: '' },
  type: { type: String, default: 'text' },
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <SettingsItem :icon="icon" :label="label" :description="description" :divider="divider">
    <template #right>
      <input
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        @input="emit('update:modelValue', $event.target.value)"
        class="text-right text-sm text-slate-700 bg-transparent border-0 outline-none focus:outline-none focus:ring-0 placeholder:text-slate-400 min-w-0 w-48 max-w-full px-2 py-1 rounded hover:bg-slate-50 focus:bg-slate-50 transition-colors"
      />
    </template>
  </SettingsItem>
</template>

<style scoped>
/* 输入框样式 */
input {
  font-family: inherit;
}
</style>