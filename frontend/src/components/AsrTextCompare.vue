<template>
  <div class="text-compare">
    <div class="text-compare__row">
      <span class="text-compare__label">Ref</span>
      <div class="text-compare__content">
        <template v-if="ops.length">
          <span v-for="(op, idx) in ops" :key="`r-${idx}`">
            <span v-if="op.op === 'H'">{{ op.ref }}</span>
            <span v-else-if="op.op === 'S'" class="err-ref" :title="`替换: ${op.ref} → ${op.hyp}`">{{ op.ref }}</span>
            <span v-else-if="op.op === 'D'" class="err-char" :title="`漏识别: ${op.ref}`">{{ op.ref }}</span>
          </span>
        </template>
        <span v-else>{{ refText || '-' }}</span>
      </div>
    </div>
    <div class="text-compare__row">
      <span class="text-compare__label">预测</span>
      <div class="text-compare__content">
        <template v-if="ops.length">
          <span v-for="(op, idx) in ops" :key="`h-${idx}`">
            <span v-if="op.op === 'H'">{{ op.hyp }}</span>
            <span v-else-if="op.op === 'S'" class="err-char" :title="`替换: ${op.ref} → ${op.hyp}`">{{ op.hyp }}</span>
            <span v-else-if="op.op === 'I'" class="err-char" :title="`多识别: ${op.hyp}`">{{ op.hyp }}</span>
            <span v-else-if="op.op === 'D'" class="err-char" :title="`漏识别: ${op.ref}`">[漏]</span>
          </span>
        </template>
        <span v-else>{{ hypText || '-' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  refText: { type: String, default: '' },
  hypText: { type: String, default: '' },
  errorsJson: { type: Object, default: null }
})

const ops = computed(() => props.errorsJson?.ops || [])
</script>
