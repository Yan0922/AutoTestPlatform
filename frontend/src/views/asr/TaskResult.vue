<template>
  <div class="page-card sticky-page">
    <PageHeader :title="taskInfo?.name">
      <template #meta>
        <span class="meta-item">模型：{{ taskInfo?.model_name }}</span>
        <span class="meta-item">创建：{{ taskInfo?.created_at }}</span>
        <span class="meta-item">完成：{{ taskInfo?.finished_at || '-' }}</span>
      </template>
    </PageHeader>

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
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AsrTextCompare from '@/components/AsrTextCompare.vue'
import PageHeader from '@/components/PageHeader.vue'
import { TaskAPI } from '@/api/asr'
import { formatDuration } from '@/utils/format'
import { useSplitPane } from '@/composables/useSplitPane'
import { useStickyTable } from '@/composables/useStickyTable'

const route = useRoute()
const taskId = Number(route.params.id)
const loading = ref(false)
const taskInfo = ref(null)
const datasets = ref([])
const results = ref([])
const currentDsId = ref(null)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const splitRootRef = ref(null)
const { leftWidth, dragging, startResize } = useSplitPane('asr-task-result-split', 280)
const { tableWrapRef, tableHeight, updateTableHeight } = useStickyTable()

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
    const data = await TaskAPI.result(taskId, params)
    taskInfo.value = data.task
    datasets.value = data.datasets
    results.value = data.audio_results || []
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

onMounted(() => fetchData())

onMounted(() => {
  window.addEventListener('split-pane-resize', updateTableHeight)
})
onUnmounted(() => {
  window.removeEventListener('split-pane-resize', updateTableHeight)
})
</script>

<style scoped>
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
