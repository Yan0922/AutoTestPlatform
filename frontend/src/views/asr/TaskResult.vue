<template>
  <div class="page-card sticky-page">
    <PageHeader :title="rootTask?.name || taskInfo?.name">
      <template #meta>
        <span class="meta-item">模型：{{ (rootTask || taskInfo)?.model_name }}</span>
        <span class="meta-item">创建：{{ (rootTask || taskInfo)?.created_at }}</span>
        <span v-if="taskInfo?.id !== rootTask?.id" class="meta-item">
          当前运行：{{ taskInfo?.created_at }}
        </span>
        <span class="meta-item">完成：{{ taskInfo?.finished_at || '-' }}</span>
      </template>
      <template #extra>
        <div class="result-actions">
          <el-button type="primary" :loading="exporting" :disabled="!canExport" @click="downloadExport">
            下载结果
          </el-button>
          <template v-if="runGroup.length > 1">
            <div
              v-for="run in runGroup"
              :key="run.id"
              class="run-link-item"
            >
              <span
                :class="['run-link', run.is_current ? 'is-current' : '']"
                @click="goRunResult(run)"
              >
                {{ run.label }}
              </span>
              <span v-if="run.started_at" class="run-time">({{ run.started_at }})</span>
            </div>
          </template>
        </div>
      </template>
    </PageHeader>

    <el-alert
      v-if="taskInfo?.task_status === 3 && taskInfo?.error_message"
      type="warning"
      :closable="false"
      class="task-error-banner"
      show-icon
      :title="taskInfo.error_message"
    />

    <div
      ref="splitRootRef"
      class="sticky-body result-split"
      data-split-root="asr-task-result-split"
      v-loading="loading"
    >
      <aside class="result-split__left sticky-col-scroll" :style="{ width: `${leftWidth}px` }">
        <div
          v-for="d in datasets"
          :key="d.id"
          :class="['ds-card', currentDsId === d.dataset ? 'active' : '']"
          @click="switchDataset(d.dataset)"
        >
          <h4>{{ d.dataset_name }}</h4>
          <div class="row"><span>音频总数</span><b>{{ d.total_audio }}</b></div>
          <div class="row"><span>总时长</span><b>{{ formatDuration(d.total_duration) }}</b></div>
          <div class="row"><span>平均WER</span><b>{{ (d.avg_wer * 100).toFixed(2) }}%</b></div>
          <div class="row"><span>RET</span><b>{{ (d.ret * 100).toFixed(2) }}%</b></div>
          <div class="row"><span>S</span><b>{{ d.s_cnt }}</b></div>
          <div class="row"><span>I</span><b>{{ d.i_cnt }}</b></div>
          <div class="row"><span>D</span><b>{{ d.d_cnt }}</b></div>
          <div class="row"><span>Hit</span><b>{{ d.hit_cnt }}</b></div>
        </div>
      </aside>

      <div
        class="result-split__handle"
        :class="{ 'is-dragging': dragging }"
        title="拖拽调节左右宽度"
        @mousedown="onResizeStart"
      />

      <section class="result-split__right sticky-col">
        <div ref="tableWrapRef" class="sticky-table-wrap result-table-wrap">
          <el-table :data="results" border stripe :height="tableHeight">
            <el-table-column prop="audio_name" label="音频名称" width="120" fixed="left" />
            <el-table-column label="播放" width="200">
              <template #default="{ row }">
                <audio :src="row.audio_path" controls preload="metadata" style="height:32px;width:100%;" />
              </template>
            </el-table-column>
            <el-table-column label="WER" width="80" align="center">
              <template #default="{ row }">{{ (row.wer * 100).toFixed(2) }}%</template>
            </el-table-column>
            <el-table-column label="文本对比" min-width="480">
              <template #default="{ row }">
                <AsrTextCompare
                  :ref-text="row.ref_text"
                  :hyp-text="row.hyp_text"
                  :errors-json="row.errors_json"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="pager sticky-pager">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next"
            :total="total"
            :page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :current-page="page"
            @current-change="onPage"
            @size-change="onPageSizeChange"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AsrTextCompare from '@/components/AsrTextCompare.vue'
import PageHeader from '@/components/PageHeader.vue'
import { TaskAPI } from '@/api/asr'
import { formatDuration } from '@/utils/format'
import { useSplitPane } from '@/composables/useSplitPane'
import { useStickyTable } from '@/composables/useStickyTable'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => Number(route.params.id))
const runId = computed(() => {
  const raw = route.query.run_id
  return raw ? Number(raw) : null
})
const loading = ref(false)
const taskInfo = ref(null)
const rootTask = ref(null)
const datasets = ref([])
const results = ref([])
const runGroup = ref([])
const currentDsId = ref(null)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const exporting = ref(false)
const splitRootRef = ref(null)
const { leftWidth, dragging, startResize } = useSplitPane('asr-task-result-split', 280)
const { tableWrapRef, tableHeight, updateTableHeight } = useStickyTable()

const canExport = computed(() => {
  if (!taskInfo.value || taskInfo.value.task_status === 1) return false
  return datasets.value.some((d) => d.total_audio > 0)
})

async function downloadExport() {
  exporting.value = true
  try {
    const params = {}
    if (runId.value) params.run_id = runId.value
    await TaskAPI.exportResults(taskId.value, params)
    ElMessage.success('结果已下载')
  } catch (err) {
    if (err.response?.data instanceof Blob) {
      const text = await err.response.data.text()
      try {
        const json = JSON.parse(text)
        ElMessage.error(json.detail || '导出失败')
      } catch {
        ElMessage.error('导出失败')
      }
    }
  } finally {
    exporting.value = false
  }
}

function goRunResult(run) {
  if (run.is_current) return
  router.push({
    name: 'asr-task-result',
    params: { id: run.root_id || taskId.value },
    query: { run_id: run.id }
  })
}

function onResizeStart(e) {
  startResize(e, splitRootRef.value?.clientWidth)
}

async function fetchData(dsId, resetPage = false) {
  if (resetPage) page.value = 1
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    const targetDs = dsId ?? currentDsId.value
    if (targetDs) params.dataset_id = targetDs
    if (runId.value) params.run_id = runId.value
    const data = await TaskAPI.result(taskId.value, params)
    taskInfo.value = data.task
    rootTask.value = data.root_task || data.task
    datasets.value = data.datasets
    results.value = data.audio_results || []
    runGroup.value = data.run_group || []
    total.value = data.audio_results_count ?? results.value.length
    if (data.page) page.value = data.page
    if (data.page_size) pageSize.value = data.page_size
    currentDsId.value = targetDs || datasets.value[0]?.dataset
  } finally {
    loading.value = false
    updateTableHeight()
  }
}

function switchDataset(id) {
  if (id === currentDsId.value) return
  fetchData(id, true)
}

function onPage(p) {
  page.value = p
  fetchData()
}

function onPageSizeChange(size) {
  pageSize.value = size
  page.value = 1
  fetchData()
}

watch([taskId, runId], () => {
  page.value = 1
  currentDsId.value = null
  fetchData(null, true)
})

onMounted(() => fetchData())

onMounted(() => {
  window.addEventListener('split-pane-resize', updateTableHeight)
})
onUnmounted(() => {
  window.removeEventListener('split-pane-resize', updateTableHeight)
})
</script>

<style scoped>
.task-error-banner {
  margin-bottom: 12px;
}

.result-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.run-link-item {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.run-link {
  font-size: 13px;
  color: #409eff;
  cursor: pointer;
  white-space: nowrap;
  border-bottom: 1px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}

.run-time {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.run-link:hover {
  border-bottom-color: #409eff;
}

.run-link.is-current {
  color: #303133;
  font-weight: 600;
  cursor: default;
  border-bottom-color: #303133;
}

.ds-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all .2s;
}
.ds-card:hover { border-color: #409EFF; }
.ds-card.active { border-color: #409EFF; box-shadow: 0 0 0 2px rgba(64,158,255,.15); }
.ds-card h4 { margin: 0 0 8px; }
.ds-card .row { display: flex; justify-content: space-between; font-size: 13px; padding: 2px 0; }
.ds-card .row span { color: #909399; }

.result-split {
  display: flex;
  min-height: 0;
  height: 100%;
}

.result-split__left {
  flex-shrink: 0;
  padding-right: 4px;
}

.result-split__handle {
  flex-shrink: 0;
  width: 6px;
  margin: 0 2px;
  border-radius: 3px;
  cursor: col-resize;
  background: #e4e7ed;
  transition: background 0.15s;
}

.result-split__handle:hover,
.result-split__handle.is-dragging {
  background: #409eff;
}

.result-split__right {
  flex: 1;
  min-width: 0;
}

.result-table-wrap :deep(.el-table .cell) {
  overflow: visible;
  text-overflow: clip;
  white-space: normal;
}
</style>
