import { onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ModelAPI } from '@/api/asr'

/** 跨页面共享：模型远程下载任务状态 */
const activeJob = ref(null)
let pollTimer = null
let pollListeners = 0

function isTerminal(status) {
  return ['completed', 'failed', 'cancelled', 'idle'].includes(status)
}

async function fetchStatus(jobId) {
  const data = await ModelAPI.remoteDownloadStatus(jobId)
  if (data?.status === 'idle' && !jobId) {
    activeJob.value = null
    return null
  }
  activeJob.value = data
  return data
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function startPolling(jobId, { onDone } = {}) {
  stopPolling()
  const tick = async () => {
    try {
      const data = await fetchStatus(jobId)
      if (!data || isTerminal(data.status)) {
        stopPolling()
        onDone?.(data)
      }
    } catch {
      /* 轮询失败不打断，下次重试 */
    }
  }
  tick()
  pollTimer = setInterval(tick, 1000)
}

export function useRemoteModelDownload() {
  onUnmounted(() => {
    pollListeners -= 1
    if (pollListeners <= 0) {
      pollListeners = 0
      stopPolling()
    }
  })

  pollListeners += 1

  async function resumeIfRunning() {
    const data = await fetchStatus()
    if (data?.status === 'running') {
      startPolling(data.job_id)
    }
    return data
  }

  async function startDownload(payload, { onDone } = {}) {
    const data = await ModelAPI.remoteDownloadStart(payload)
    activeJob.value = data
    startPolling(data.job_id, {
      onDone: (finalData) => {
        if (finalData?.status === 'completed') {
          ElMessage.success(
            `下载完成：成功 ${finalData.ok}，跳过 ${finalData.skipped}，失败 ${finalData.failed}`
          )
        } else if (finalData?.status === 'cancelled') {
          ElMessage.info('下载已取消')
        } else if (finalData?.status === 'failed') {
          ElMessage.error(finalData.message || finalData.error || '下载失败')
        }
        onDone?.(finalData)
      }
    })
    return data
  }

  async function cancelDownload() {
    const job = activeJob.value
    if (!job?.job_id || job.status !== 'running') return
    await ModelAPI.remoteDownloadCancel(job.job_id)
    await fetchStatus(job.job_id)
    stopPolling()
  }

  return {
    activeJob,
    startDownload,
    cancelDownload,
    resumeIfRunning,
    fetchStatus,
    stopPolling
  }
}
