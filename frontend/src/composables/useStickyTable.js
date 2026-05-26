import { onMounted, onUnmounted, ref, watch } from 'vue'

/** 表格区域内部滚动，工具栏与表头保持可见 */
export function useStickyTable(minHeight = 240) {
  const tableWrapRef = ref(null)
  const tableHeight = ref(480)
  let observer = null

  function updateTableHeight() {
    if (!tableWrapRef.value) return
    tableHeight.value = Math.max(tableWrapRef.value.clientHeight, minHeight)
  }

  function bindObserver(el) {
    observer?.disconnect()
    observer = null
    if (!el) return
    observer = new ResizeObserver(updateTableHeight)
    observer.observe(el)
    updateTableHeight()
  }

  onMounted(() => {
    bindObserver(tableWrapRef.value)
    window.addEventListener('resize', updateTableHeight)
  })

  watch(tableWrapRef, bindObserver)

  onUnmounted(() => {
    observer?.disconnect()
    window.removeEventListener('resize', updateTableHeight)
  })

  return { tableWrapRef, tableHeight, updateTableHeight }
}
