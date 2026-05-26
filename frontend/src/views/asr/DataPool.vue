<template>
  <div class="page-card sticky-page">
    <div class="toolbar sticky-toolbar">
      <el-input v-model="filters.name" placeholder="按名称模糊搜索" clearable style="width:200px;" @change="reload" />
      <el-select v-model="filters.language" multiple collapse-tags collapse-tags-tooltip placeholder="语种" clearable style="width:140px;" @change="onFilterChange">
        <el-option v-for="l in LANGUAGES" :key="l.value" :label="l.label" :value="l.value" />
      </el-select>
      <el-select v-model="filters.source" multiple collapse-tags collapse-tags-tooltip placeholder="来源" clearable style="width:140px;" @change="onFilterChange">
        <el-option v-for="o in SOURCES" :key="o" :label="o" :value="o" />
      </el-select>
      <el-select v-model="filters.industry" multiple collapse-tags collapse-tags-tooltip placeholder="行业" clearable style="width:140px;" @change="onFilterChange">
        <el-option v-for="o in INDUSTRIES" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-select v-model="filters.noise" multiple collapse-tags collapse-tags-tooltip placeholder="噪声" clearable style="width:140px;" @change="onFilterChange">
        <el-option v-for="o in NOISES" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-input-number v-model="filters.duration_min" :min="0" placeholder="时长≥" style="width:120px;" @change="reload" />
      <el-input-number v-model="filters.duration_max" :min="0" placeholder="时长≤" style="width:120px;" @change="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetFilter">重置</el-button>
      <el-divider direction="vertical" />
      <el-button type="success" @click="importVisible = true">批量导入</el-button>
      <el-button @click="downloadTemplate">下载模板</el-button>
      <el-button type="danger" :disabled="!selected.length" @click="batchDelete">删除选中</el-button>
      <el-button type="warning" :disabled="!selected.length" @click="openJoin">加入数据集</el-button>
    </div>

    <div ref="tableWrapRef" class="sticky-table-wrap">
      <el-table
        :data="rows" border stripe v-loading="loading"
        :height="tableHeight"
        @selection-change="(r) => selected = r"
      >
      <el-table-column type="selection" width="46" />
      <el-table-column prop="name" label="音频名称" min-width="100" />
      <el-table-column prop="language_display" label="语种" width="70" align="center" />
      <el-table-column label="播放" width="240">
        <template #default="{ row }">
          <audio :src="row.audio_path" controls preload="metadata" style="height:32px;width:100%;" />
        </template>
      </el-table-column>
      <el-table-column label="时长" width="100">
        <template #default="{ row }">{{ formatDuration(row.duration) }}</template>
      </el-table-column>
      <el-table-column prop="source" label="来源" width="100" />
      <el-table-column prop="noise_display" label="噪声" width="80" />
      <el-table-column prop="industry_display" label="行业" width="90" />
      <el-table-column label="文本" min-width="240">
        <template #default="{ row }">
          <div v-if="editingId !== row.id" @click="startEdit(row)" style="cursor:text;">
            <el-tooltip :content="row.ref_text" placement="top" :show-after="300">
              <div style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
                {{ row.ref_text || '点击编辑文本' }}
              </div>
            </el-tooltip>
          </div>
          <div v-else>
            <el-input v-model="editingText" type="textarea" :rows="3" @blur="cancelEdit" />
            <el-button size="small" type="primary" style="margin-top:4px;" @mousedown.prevent="confirmEdit(row)">OK</el-button>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="关联数据集" width="160">
        <template #default="{ row }">
          <el-tag v-for="n in row.dataset_names" :key="n" type="info" size="small" style="margin-right:4px;">{{ n }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="removeOne(row)">删除</el-button>
          <el-button size="small" type="warning" @click="openJoinOne(row)">加入</el-button>
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

    <!-- 编辑音频 -->
    <el-dialog v-model="editVisible" title="编辑音频" width="520px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="音频名称" required>
          <el-input v-model="editForm.name" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="editForm.source" style="width:100%;">
            <el-option v-for="o in SOURCES" :key="o" :label="o" :value="o" />
          </el-select>
        </el-form-item>
        <el-form-item label="噪声">
          <el-select v-model="editForm.noise" style="width:100%;">
            <el-option v-for="o in NOISES" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="行业">
          <el-select v-model="editForm.industry" style="width:100%;">
            <el-option v-for="o in INDUSTRIES" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联数据集">
          <el-select v-model="editForm.dataset_ids" multiple filterable placeholder="可多选" style="width:100%;">
            <el-option v-for="d in allDatasets" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="submitEdit">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- 加入数据集 -->
    <el-dialog v-model="joinVisible" title="选择要加入的数据集" width="460px">
      <el-input v-model="joinSearch" placeholder="按名字过滤" clearable style="margin-bottom:8px;" />
      <el-checkbox-group v-model="joinSelected">
        <div v-for="d in filteredDatasets" :key="d.id" style="padding:4px 0;">
          <el-checkbox :value="d.id">{{ d.name }}（{{ d.created_at }}）</el-checkbox>
        </div>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="joinVisible = false">取消</el-button>
        <el-button type="primary" @click="submitJoin">确认</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog v-model="importVisible" title="批量导入音频" width="800px">
      <input ref="excelInput" type="file" accept=".xlsx" @change="onExcelChange" />
      <div v-if="previewRows.length" style="margin-top:10px;">
        <el-table :data="previewRows" border max-height="320" size="small">
          <el-table-column prop="name" label="名称" min-width="140" />
          <el-table-column prop="language" label="语种" width="70" />
          <el-table-column prop="audio_path" label="路径" min-width="160" />
          <el-table-column prop="source" label="来源" width="80" />
          <el-table-column prop="noise" label="噪声" width="80" />
          <el-table-column prop="industry" label="行业" width="80" />
          <el-table-column label="时长(自动)" width="100">
            <template #default="{ row }">{{ row.duration ? formatDuration(row.duration) : '-' }}</template>
          </el-table-column>
          <el-table-column prop="ref_text" label="文本" min-width="160" />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!previewRows.length" @click="submitImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { AudioAPI, DatasetAPI } from '@/api/asr'
import { formatDuration } from '@/utils/format'
import { buildListParams } from '@/utils/query'
import { useStickyTable } from '@/composables/useStickyTable'

const LANGUAGES = [
  { value: 'zh', label: '中' }, { value: 'en', label: '英' }, { value: 'es', label: '西' },
  { value: 'ja', label: '日' }, { value: 'ko', label: '韩' }, { value: 'ru', label: '俄' },
  { value: 'fr', label: '法' }, { value: 'de', label: '德' }, { value: 'th', label: '泰' },
  { value: 'it', label: '意' }, { value: 'ar', label: '阿' }
]
const SOURCES = ['Sota1', 'Sota2', 'Sota3', 'gf', 'outside', 'cv15', '30min']
const NOISES = [
  { value: 'quiet', label: '安静' }, { value: 'low_mid', label: '中低' },
  { value: 'mid_high', label: '中高' }, { value: 'high', label: '高噪' }
]
const INDUSTRIES = [
  { value: 'unknown', label: '未知' }, { value: 'economy', label: '经济' },
  { value: 'finance', label: '金融' }, { value: 'medical', label: '医疗' },
  { value: 'travel', label: '旅游' }, { value: 'food', label: '美食' },
  { value: 'technology', label: '科技' }
]

const filters = reactive({ name: '', language: [], source: [], industry: [], noise: [], duration_min: null, duration_max: null })
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const selected = ref([])
const { tableWrapRef, tableHeight, updateTableHeight } = useStickyTable()

async function reload() {
  loading.value = true
  try {
    const params = buildListParams(filters, { page: page.value, page_size: pageSize.value })
    const data = await AudioAPI.list(params)
    rows.value = data.results || []
    total.value = data.count || 0
  } finally {
    loading.value = false
    updateTableHeight()
  }
}
function onFilterChange() {
  page.value = 1
  reload()
}
function onPage(p) { page.value = p; reload() }
function onPageSizeChange(size) {
  pageSize.value = size
  page.value = 1
  reload()
}
function resetFilter() {
  Object.assign(filters, { name: '', language: [], source: [], industry: [], noise: [], duration_min: null, duration_max: null })
  page.value = 1
  reload()
}
onMounted(reload)

async function removeOne(row) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.name}」?`, '提示', { type: 'warning' })
  } catch { return }
  await AudioAPI.remove(row.id)
  ElMessage.success('已删除')
  reload()
}
async function batchDelete() {
  try {
    await ElMessageBox.confirm(`确认删除选中 ${selected.value.length} 条数据?`, '提示', { type: 'warning' })
  } catch { return }
  await AudioAPI.batchDelete(selected.value.map(r => r.id))
  ElMessage.success('已删除')
  reload()
}

const editingId = ref(0)
const editingText = ref('')
function startEdit(row) { editingId.value = row.id; editingText.value = row.ref_text }
function cancelEdit() { editingId.value = 0 }
async function confirmEdit(row) {
  await AudioAPI.updateText(row.id, editingText.value)
  row.ref_text = editingText.value
  editingId.value = 0
  ElMessage.success('已保存')
}

// 编辑音频信息
const editVisible = ref(false)
const editSubmitting = ref(false)
const editForm = reactive({
  id: 0,
  name: '',
  source: 'outside',
  noise: 'quiet',
  industry: 'unknown',
  dataset_ids: []
})

async function openEdit(row) {
  await loadAllDatasets()
  Object.assign(editForm, {
    id: row.id,
    name: row.name,
    source: row.source,
    noise: row.noise,
    industry: row.industry,
    dataset_ids: [...(row.dataset_ids || [])]
  })
  editVisible.value = true
}

async function submitEdit() {
  if (!editForm.name.trim()) {
    ElMessage.warning('请输入音频名称')
    return
  }
  editSubmitting.value = true
  try {
    await AudioAPI.updateInfo(editForm.id, {
      name: editForm.name.trim(),
      source: editForm.source,
      noise: editForm.noise,
      industry: editForm.industry,
      dataset_ids: editForm.dataset_ids
    })
    ElMessage.success('修改成功')
    editVisible.value = false
    reload()
  } finally {
    editSubmitting.value = false
  }
}

// 加入数据集
const joinVisible = ref(false)
const joinSelected = ref([])
const allDatasets = ref([])
const joinSearch = ref('')
const joinAudioIds = ref([])

async function loadAllDatasets() {
  const data = await DatasetAPI.list({ page: 1, page_size: 200 })
  allDatasets.value = data.results || []
}
const filteredDatasets = computed(() => {
  if (!joinSearch.value) return allDatasets.value
  return allDatasets.value.filter(d => d.name.includes(joinSearch.value))
})
async function openJoin() {
  joinAudioIds.value = selected.value.map(r => r.id)
  joinSelected.value = []
  await loadAllDatasets()
  joinVisible.value = true
}
async function openJoinOne(row) {
  joinAudioIds.value = [row.id]
  joinSelected.value = []
  await loadAllDatasets()
  joinVisible.value = true
}
async function submitJoin() {
  if (!joinSelected.value.length) { ElMessage.warning('请选择数据集'); return }
  await AudioAPI.joinDataset(joinAudioIds.value, joinSelected.value)
  ElMessage.success('已加入')
  joinVisible.value = false
  reload()
}

// 批量导入
const importVisible = ref(false)
const previewRows = ref([])
const excelInput = ref()
function downloadTemplate() {
  window.open(AudioAPI.templateUrl, '_blank')
}
async function onExcelChange(e) {
  const f = e.target.files?.[0]
  if (!f) return
  const data = await AudioAPI.parseExcel(f)
  previewRows.value = data.rows || []
}
async function submitImport() {
  const r = await AudioAPI.import(previewRows.value)
  ElMessage.success(`导入成功 ${r.count} 条`)
  importVisible.value = false
  previewRows.value = []
  if (excelInput.value) excelInput.value.value = ''
  reload()
}
</script>
