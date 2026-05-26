<template>
  <div class="page-card sticky-page">
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
      <el-table-column label="任务状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.task_status === 1" type="warning">进行中</el-tag>
          <el-tag v-else-if="row.task_status === 2" type="success">运行完成</el-tag>
          <el-tag v-else type="danger">失败</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" :disabled="row.task_status !== 2" @click="openResult(row)">运行结果</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
      </el-table>
    </div>
    <div class="pager sticky-pager">
      <el-pagination background layout="prev, pager, next, total"
        :total="total" :page-size="15" :current-page="page" @current-change="onPage" />
    </div>

    <!-- 创建任务 -->
    <el-dialog v-model="createVisible" title="创建任务" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="任务名称" required>
          <el-input v-model="form.name" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="模型" required>
          <el-select v-model="form.model" filterable placeholder="选择模型" style="width:100%;">
            <el-option v-for="m in models" :key="m.id" :label="`${m.name} (${m.version})`" :value="m.id" />
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { DatasetAPI, ModelAPI, TaskAPI } from '@/api/asr'
import { useStickyTable } from '@/composables/useStickyTable'

const router = useRouter()
const rows = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const { tableWrapRef, tableHeight, updateTableHeight } = useStickyTable()
async function reload() {
  loading.value = true
  try {
    const data = await TaskAPI.list({ page: page.value, page_size: 15 })
    rows.value = data.results || []
    total.value = data.count || 0
  } finally {
    loading.value = false
    updateTableHeight()
  }
}
function onPage(p) { page.value = p; reload() }
onMounted(reload)

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
    ElMessage.warning('请完整填写'); return
  }
  submitting.value = true
  try {
    await TaskAPI.create(form)
    ElMessage.success('任务已提交')
    createVisible.value = false
    reload()
  } finally { submitting.value = false }
}

function openResult(row) {
  const r = router.resolve({ name: 'asr-task-result', params: { id: row.id } })
  window.open(r.href, '_blank')
}
async function remove(row) {
  try { await ElMessageBox.confirm('确认删除该任务?', '提示', { type: 'warning' }) } catch { return }
  await TaskAPI.remove(row.id)
  ElMessage.success('已删除')
  reload()
}
</script>
