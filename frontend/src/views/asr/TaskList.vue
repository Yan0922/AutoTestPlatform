<template>
  <div class="page-card sticky-page">
    <el-alert
      v-if="runningCount > 0"
      type="info"
      :closable="false"
      class="task-running-banner"
      show-icon
    >
      <template #title>
        有 {{ runningCount }} 个任务正在后台运行（K2 推理可能需要数分钟）
      </template>
      <div class="task-running-hint">列表会自动刷新；完成后状态会变为「运行完成」或「失败」。</div>
    </el-alert>

    <div class="toolbar sticky-toolbar">
      <el-button type="primary" @click="openCreate">创建任务</el-button>
      <el-button @click="reload">刷新</el-button>
    </div>
    <div ref="tableWrapRef" class="sticky-table-wrap">
      <el-table :data="rows" border stripe v-loading="loading" :height="tableHeight">
      <el-table-column prop="name" label="任务名称" min-width="160" />
      <el-table-column prop="model_name" label="模型名字" min-width="140" />
      <el-table-column label="数据集" min-width="160">
        <template #default="{ row }">
          <el-tag v-for="n in row.dataset_names" :key="n" size="small" style="margin-right:4px;">{{ n }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="任务状态" width="120" class-name="task-status-cell">
        <template #default="{ row }">
          <el-tag v-if="row.task_status === 1" type="warning">
            <el-icon v-if="pollTimer" class="is-loading status-loading-icon"><Loading /></el-icon>
            进行中
          </el-tag>
          <el-tag v-else-if="row.task_status === 2" type="success">运行完成</el-tag>
          <el-tag v-else type="danger">失败</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" :disabled="row.task_status === 1" @click="openResult(row)">运行结果</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
      </el-table>
    </div>
    <div class="pager sticky-pager">
      <el-pagination background layout="prev, pager, next, total"
        :total="total" :page-size="15" :current-page="page" @current-change="onPage" />
    </div>

    <!-- 创建任务：提交后立即关闭，任务在后台运行 -->
    <el-dialog
      v-model="createVisible"
      title="创建任务"
      width="520px"
      :close-on-click-modal="!submitting"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="任务名称" required>
          <el-input
            v-model="form.name"
            maxlength="16"
            show-word-limit
            placeholder="例如 test"
          />
          <div class="name-hint">提交后自动追加时间，如：test_20260527_1438</div>
        </el-form-item>
        <el-form-item label="模型" required>
          <el-select v-model="form.model" filterable placeholder="选择模型" style="width:100%;">
            <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据集" required>
          <el-select v-model="form.dataset_ids" multiple filterable placeholder="选择一个或多个数据集" style="width:100%;">
            <el-option v-for="d in datasets" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { DatasetAPI, ModelAPI, TaskAPI } from '@/api/asr'
import { useStickyTable } from '@/composables/useStickyTable'

const router = useRouter()
const rows = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const pollTimer = ref(null)
const { tableWrapRef, tableHeight, updateTableHeight } = useStickyTable()

const runningCount = computed(() => rows.value.filter((r) => r.task_status === 1).length)

async function reload(silent = false) {
  if (!silent) loading.value = true
  try {
    const data = await TaskAPI.list({ page: page.value, page_size: 15 })
    const prevRunning = runningCount.value
    rows.value = data.results || []
    total.value = data.count || 0
    syncPollTimer()
    if (silent && prevRunning > 0 && runningCount.value === 0) {
      const last = rows.value[0]
      if (last?.task_status === 2) {
        ElMessage.success(`任务「${last.name}」已完成`)
      } else if (last?.task_status === 3) {
        ElMessage.error(last.error_message || `任务「${last.name}」失败`)
      }
    }
  } finally {
    if (!silent) loading.value = false
    updateTableHeight()
  }
}

function syncPollTimer() {
  if (runningCount.value > 0 && !pollTimer.value) {
    pollTimer.value = setInterval(() => reload(true), 3000)
  } else if (runningCount.value === 0 && pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

function onPage(p) { page.value = p; reload() }

onMounted(() => {
  reload()
})

onUnmounted(() => {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
})

const createVisible = ref(false)
const submitting = ref(false)
const form = reactive({ name: '', model: null, dataset_ids: [] })
const models = ref([])
const datasets = ref([])

async function openCreate() {
  const [m, d] = await Promise.all([
    ModelAPI.list({ page: 1, page_size: 500 }),
    DatasetAPI.list({ page: 1, page_size: 500 })
  ])
  models.value = m.results || []
  datasets.value = d.results || []
  Object.assign(form, { name: '', model: null, dataset_ids: [] })
  createVisible.value = true
}

async function submit() {
  if (!form.name || !form.model || !form.dataset_ids.length) {
    ElMessage.warning('请完整填写')
    return
  }
  submitting.value = true
  try {
    await TaskAPI.create(form)
    createVisible.value = false
    ElMessage.success('任务已提交，正在后台运行')
    await reload(true)
    syncPollTimer()
  } finally {
    submitting.value = false
  }
}

function openResult(row) {
  router.push({ name: 'asr-task-result', params: { id: row.id } })
}

async function remove(row) {
  try { await ElMessageBox.confirm('确认删除该任务?', '提示', { type: 'warning' }) } catch { return }
  await TaskAPI.remove(row.id)
  ElMessage.success('已删除')
  reload()
}
</script>

<style scoped>
.task-running-banner {
  margin-bottom: 12px;
}
.task-running-hint {
  margin-top: 4px;
  font-size: 13px;
  color: #606266;
}
.name-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

/* 状态列含 Tag + 图标，避免 el-table 默认 ellipsis 截断出 ··· */
:deep(.task-status-cell .cell) {
  overflow: visible;
  text-overflow: clip;
}

.status-loading-icon {
  vertical-align: -2px;
  margin-right: 2px;
}
</style>
