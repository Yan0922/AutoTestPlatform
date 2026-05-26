/** 秒数转为 hh:mm:ss，例如 472.14 -> 00:07:52 */
export function formatDuration(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0))
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  return [h, m, s].map((n) => String(n).padStart(2, '0')).join(':')
}

/** 文件大小，例如 2843880 -> "2,778KB"，69571353 -> "66MB" */
export function formatFileSize(bytes) {
  if (bytes == null || bytes === '') return '-'
  const n = Number(bytes)
  if (!Number.isFinite(n) || n < 0) return '-'
  if (n === 0) return '0KB'

  const KB = 1024
  const MB = KB * 1024
  const GB = MB * 1024

  if (n < KB) return '1KB'
  if (n < MB) return `${Math.round(n / KB).toLocaleString('en-US')}KB`
  if (n < GB) return `${Math.round(n / MB).toLocaleString('en-US')}MB`
  return `${Math.round((n / GB) * 100) / 100}GB`
}
