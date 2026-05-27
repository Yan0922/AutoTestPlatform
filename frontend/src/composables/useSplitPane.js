import { onMounted, onUnmounted, ref } from 'vue'

/** 左右分栏拖拽调节宽度，宽度持久化到 localStorage */
export function useSplitPane(storageKey, defaultWidth = 280, minWidth = 220, maxRatio = 0.42) {
  const leftWidth = ref(defaultWidth)
  const dragging = ref(false)

  try {
    const saved = parseInt(localStorage.getItem(storageKey), 10)
    if (saved >= minWidth) leftWidth.value = saved
  } catch {
    /* ignore */
  }

  let startX = 0
  let startWidth = 0

  function clampWidth(width, containerWidth) {
    const maxWidth = Math.max(minWidth, Math.floor(containerWidth * maxRatio))
    return Math.min(Math.max(width, minWidth), maxWidth)
  }

  function onMouseMove(e) {
    if (!dragging.value) return
    const container = document.querySelector(`[data-split-root="${storageKey}"]`)
    const containerWidth = container?.clientWidth || window.innerWidth
    leftWidth.value = clampWidth(startWidth + e.clientX - startX, containerWidth)
  }

  function onMouseUp() {
    if (!dragging.value) return
    dragging.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    try {
      localStorage.setItem(storageKey, String(leftWidth.value))
    } catch {
      /* ignore */
    }
    window.dispatchEvent(new CustomEvent('split-pane-resize'))
  }

  function startResize(e, containerWidth) {
    dragging.value = true
    startX = e.clientX
    startWidth = leftWidth.value
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    if (containerWidth) {
      leftWidth.value = clampWidth(leftWidth.value, containerWidth)
    }
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  onUnmounted(() => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  })

  return { leftWidth, dragging, startResize, clampWidth }
}
