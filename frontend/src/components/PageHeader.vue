<template>
  <div class="page-header sticky-toolbar">
    <div v-if="backPath" class="page-header__nav">
      <el-button link type="primary" :icon="ArrowLeft" @click="handleBack">
        {{ backText }}
      </el-button>
    </div>
    <h3 v-if="title" class="page-header__title">{{ title }}</h3>
    <div v-if="$slots.meta" class="page-header__meta">
      <slot name="meta" />
    </div>
    <div v-if="$slots.extra" class="page-header__extra">
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

const props = defineProps({
  title: { type: String, default: '' },
  backTo: { type: String, default: '' },
  backLabel: { type: String, default: '' }
})

const route = useRoute()
const router = useRouter()

const backPath = computed(() => props.backTo || route.meta?.back?.path || '')
const backText = computed(() => props.backLabel || route.meta?.back?.label || '返回')

function handleBack() {
  if (backPath.value) {
    router.push(backPath.value)
  } else {
    router.back()
  }
}
</script>
