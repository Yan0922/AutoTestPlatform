<template>
  <div class="page-card sticky-page">
    <el-alert
      v-if="showDownloadBanner"
      type="info"
      :closable="false"
      class="download-banner"
      show-icon
    >
      <template #title>
        <span>正在下载远程模型</span>
        <span v-if="activeJob?.current_item" class="download-banner-sub">
          {{ activeJob.current_item.language }} / {{ activeJob.current_item.size }} / {{ activeJob.current_item.version }}
        </span>
      </template>
      <div class="download-banner-body">
        <el-progress :percentage="downloadPercent" :stroke-width="14" striped striped-flow />
        <div class="download-banner-meta">
          <span>{{ downloadProgressText }}</span>
          <span v-if="downloadBytesText">{{ downloadBytesText }}</span>
          <el-button type="danger" link size="small" @click="onCancelRemoteDownload">取消下载</el-button>
        </div>
      </div>
    </el-alert>

    <div class="toolbar sticky-toolbar">
      <el-input v-model="filters.name" placeholder="按模型名称搜索" clearable style="width:200px;" @change="onFilterChange" />
      <el-select v-model="filters.language" multiple collapse-tags collapse-tags-tooltip placeholder="语种" clearable style="width:140px;" @change="onFilterChange">
        <el-option v-for="l in LANGUAGES" :key="l.value" :label="l.label" :value="l.value" />
      </el-select>
      <el-select v-model="filters.size" multiple collapse-tags collapse-tags-tooltip placeholder="尺寸" clearable style="width:140px;" @change="onFilterChange">
        <el-option v-for="s in MODEL_SIZES" :key="s.value" :label="s.label" :value="s.value" />
      </el-select>
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetFilter">重置</el-button>
      <el-button type="success" @click="uploadVisible = true">上传模型</el-button>
      <el-button type="warning" @click="openRemoteDownload">下载模型</el-button>
    </div>

    <div ref="tableWrapRef" class="sticky-table-wrap">
      <el-table :data="rows" border stripe v-loading="loading" :height="tableHeight">
      <el-table-column prop="name" label="模型名称" min-width="80" />
      <el-table-column prop="language_display" label="语种" width="120" />
      <el-table-column prop="version" label="版本" width="140" />
      <el-table-column prop="size_display" label="尺寸" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="220" />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDetail(row)">查看详情</el-button>
          <el-button size="small" type="primary" @click="openEdit(row)">修改</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
      </el-table>
    </div>

    <div class="pager sticky-pager">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="onPageChange"
      />
    </div>

    <!-- 上传弹窗 -->
    <el-dialog v-model="uploadVisible" title="上传模型" width="520px">
      <el-form ref="uploadFormRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="form.name" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item label="语种" prop="language">
          <el-select v-model="form.language">
            <el-option v-for="l in LANGUAGES" :key="l.value" :label="l.label" :value="l.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本" prop="version">
          <el-input v-model="form.version" placeholder="只填末尾数字，例如 2、12、6" maxlength="10">
            <template #prepend>{{ VERSION_PREFIX }}</template>
          </el-input>
        </el-form-item>
        <el-form-item label="尺寸" prop="size">
          <el-radio-group v-model="form.size">
            <el-radio value="base">base</el-radio>
            <el-radio value="small">small</el-radio>
            <el-radio value="large">large</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="模型文件">
          <input ref="folderInput" type="file" webkitdirectory directory multiple @change="onFolderChange" />
          <div v-if="form.files.length" style="margin-top:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;color:#909399;margin-bottom:4px;">
              <span>共 {{ form.files.length }} 个文件，总大小 {{ formatSize(totalSize) }}</span>
              <el-button size="small" type="danger" link @click="clearFiles">清空已选</el-button>
            </div>
            <el-table :data="filePreview" border size="small" max-height="220" stripe>
              <el-table-column label="序号" type="index" width="70" align="center" />
              <el-table-column prop="name" label="文件名" min-width="220" show-overflow-tooltip />
              <el-table-column label="大小" width="110" align="right">
                <template #default="{ row }">{{ formatSize(row.size) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitUpload">提交上传</el-button>
      </template>
    </el-dialog>

    <!-- 修改弹窗 -->
    <el-dialog v-model="editVisible" title="修改模型" width="480px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="模型名称"><el-input v-model="editForm.name" maxlength="30" /></el-form-item>
        <el-form-item label="模型版本">
          <el-input v-model="editForm.version" placeholder="只填末尾数字，例如 2、12、6" maxlength="10">
            <template #prepend>{{ VERSION_PREFIX }}</template>
          </el-input>
        </el-form-item>
        <el-form-item label="语种">
          <el-select v-model="editForm.language">
            <el-option v-for="l in LANGUAGES" :key="l.value" :label="l.label" :value="l.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="尺寸">
          <el-radio-group v-model="editForm.size">
            <el-radio value="base">base</el-radio>
            <el-radio value="small">small</el-radio>
            <el-radio value="large">large</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="模型详情" width="640px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="模型名称">{{ detail.name }}</el-descriptions-item>
        <el-descriptions-item label="语种">{{ detail.language_display }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ detail.version }}</el-descriptions-item>
        <el-descriptions-item label="尺寸">{{ detail.size_display }}</el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ detail.created_at }}</el-descriptions-item>
      </el-descriptions>
      <h4 style="margin-top:14px;">模型文件</h4>
      <el-table :data="detail.files || []" border size="small">
        <el-table-column prop="file_name" label="文件名" />
        <el-table-column label="大小" width="120" align="right">
          <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 远程下载模型：点右上角 X 仅关闭窗口，不中断下载 -->
    <el-dialog
      v-model="remoteVisible"
      title="从远程下载模型"
      width="720px"
      :close-on-click-modal="false"
      @closed="onRemoteDialogClosed"
    >
      <el-alert
        v-if="!remoteBaseUrl"
        type="warning"
        :closable="false"
        title="未配置远程地址"
        description="请在后端 .env 中设置 ASR_MODEL_REMOTE_BASE_URL"
        style="margin-bottom:12px;"
      />

      <el-form label-width="80px">
        <el-form-item label="语种" required>
          <el-select v-model="remoteForm.languages" multiple collapse-tags collapse-tags-tooltip placeholder="可多选" style="width:100%;">
            <el-option v-for="l in LANGUAGES" :key="l.value" :label="l.label" :value="l.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="尺寸" required>
          <el-select v-model="remoteForm.sizes" multiple collapse-tags collapse-tags-tooltip placeholder="可多选" style="width:100%;">
            <el-option v-for="s in MODEL_SIZES" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本" required>
          <el-select
            v-model="remoteForm.versions"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="请先选择语种和尺寸，自动加载可用版本"
            :loading="remoteLoading"
            :disabled="!remoteVersionOptions.length"
            style="width:100%;"
          >
            <el-option v-for="v in remoteVersionOptions" :key="v" :label="v" :value="v" />
          </el-select>
        </el-form-item>
      </el-form>

      <div v-if="remoteCatalog.errors?.length" style="margin-bottom:8px;">
        <el-alert
          v-for="(err, idx) in remoteCatalog.errors"
          :key="idx"
          type="error"
          :closable="false"
          :title="`${err.language}/${err.size} 目录读取失败`"
          :description="err.error"
          style="margin-bottom:6px;"
        />
      </div>

      <div v-if="remotePreviewItems.length" style="margin-top:8px;">
        <div style="margin-bottom:6px;color:#606266;">
          远程目录共发现 {{ remoteCatalog.items?.length || 0 }} 个包；
          按当前选择将尝试下载 <strong>{{ remoteDownloadCount }}</strong> 个组合
        </div>
        <el-table :data="remotePreviewItems" border size="small" max-height="220">
          <el-table-column prop="language" label="语种" width="70" />
          <el-table-column prop="size" label="尺寸" width="80" />
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column prop="zip_name" label="压缩包" min-width="180" />
        </el-table>
      </div>

      <div v-if="isRemoteJobActive" style="margin-top:12px;">
        <div style="margin-bottom:6px;font-weight:600;">下载进度</div>
        <el-progress :percentage="downloadPercent" :stroke-width="16" striped striped-flow />
        <div style="margin-top:8px;color:#606266;font-size:13px;">
          {{ downloadProgressText }}
          <span v-if="downloadBytesText">（{{ downloadBytesText }}）</span>
        </div>
      </div>

      <div v-if="remoteResults.length" style="margin-top:12px;">
        <div style="margin-bottom:6px;font-weight:600;">下载结果</div>
        <el-table :data="remoteResults" border size="small" max-height="200">
          <el-table-column prop="language" label="语种" width="70" />
          <el-table-column prop="size" label="尺寸" width="80" />
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'ok'" type="success" size="small">成功</el-tag>
              <el-tag v-else-if="row.status === 'skipped'" type="info" size="small">跳过</el-tag>
              <el-tag v-else type="danger" size="small">失败</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="说明" min-width="200">
            <template #default="{ row }">{{ row.message || row.error || row.name || '-' }}</template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button v-if="isRemoteJobActive" type="danger" @click="onCancelRemoteDownload">取消下载</el-button>
        <el-button v-else @click="remoteVisible = false">关闭</el-button>
        <el-button
          v-if="!isRemoteJobActive"
          :loading="remoteLoading"
          :disabled="!remoteForm.languages.length || !remoteForm.sizes.length"
          @click="loadRemoteCatalog"
        >
          刷新版本列表
        </el-button>
        <el-button
          v-if="!isRemoteJobActive"
          type="primary"
          :disabled="!remoteBaseUrl || !remoteForm.languages.length || !remoteForm.sizes.length || !remoteForm.versions.length"
          @click="submitRemoteDownload"
        >
          开始下载
        </el-button>
        <el-button v-if="isRemoteJobActive" type="primary" plain @click="remoteVisible = false">隐藏窗口</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ModelAPI } from '@/api/asr'
import { useRemoteModelDownload } from '@/composables/useRemoteModelDownload'
import { useStickyTable } from '@/composables/useStickyTable'
import { formatFileSize } from '@/utils/format'
import { buildListParams } from '@/utils/query'

const { activeJob, startDownload, cancelDownload, resumeIfRunning } = useRemoteModelDownload()

const LANGUAGES = [
  { value: 'zh', label: '中' }, { value: 'en', label: '英' }, { value: 'es', label: '西' },
  { value: 'ja', label: '日' }, { value: 'ko', label: '韩' }, { value: 'ru', label: '俄' },
  { value: 'fr', label: '法' }, { value: 'de', label: '德' }, { value: 'th', label: '泰' },
  { value: 'it', label: '意' }, { value: 'ar', label: '阿' }
]
const MODEL_SIZES = [
  { value: 'base', label: 'base' },
  { value: 'small', label: 'small' },
  { value: 'large', label: 'large' }
]

const VERSION_PREFIX = 'v1.0.0.'

function wrapVersion(suffix) {
  const s = String(suffix ?? '').trim()
  return s ? `${VERSION_PREFIX}${s}` : ''
}

function unwrapVersion(full) {
  const s = String(full ?? '')
  return s.startsWith(VERSION_PREFIX) ? s.slice(VERSION_PREFIX.length) : s
}

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 15
const loading = ref(false)
const filters = reactive({ name: '', language: [], size: [] })
const { tableWrapRef, tableHeight, updateTableHeight } = useStickyTable()

async function reload() {
  loading.value = true
  try {
    const params = buildListParams(
      { search: filters.name, language: filters.language, size: filters.size },
      { page: page.value, page_size: pageSize }
    )
    const data = await ModelAPI.list(params)
    rows.value = data.results || []
    total.value = data.count || 0
  } finally {
    loading.value = false
    updateTableHeight()
  }
}
function resetFilter() {
  Object.assign(filters, { name: '', language: [], size: [] })
  page.value = 1
  reload()
}
function onFilterChange() {
  page.value = 1
  reload()
}
function onPageChange(p) { page.value = p; reload() }
onMounted(async () => {
  await reload()
  const job = await resumeIfRunning()
  if (job?.status === 'running') {
    syncRemoteResultsFromJob(job)
  }
})

const uploadVisible = ref(false)
const submitting = ref(false)
const uploadFormRef = ref()
const folderInput = ref()
const form = reactive({ name: '', language: 'zh', version: '', size: 'base', files: [] })
const rules = {
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  version: [
    { required: true, message: '请输入版本末尾数字', trigger: 'blur' },
    { pattern: /^\d+$/, message: '版本末尾只能是数字', trigger: 'blur' }
  ]
}
function formatSize(bytes) {
  if (bytes == null) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let v = Number(bytes)
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++ }
  return `${v.toFixed(i === 0 ? 0 : 2)} ${units[i]}`
}

const totalSize = computed(() => form.files.reduce((sum, f) => sum + (f.size || 0), 0))

const filePreview = computed(() => form.files.map(f => {
  const rel = f.webkitRelativePath || f.name || ''
  const pureName = rel.split('/').pop() || rel
  return { name: pureName, size: f.size }
}))

function onFolderChange(e) {
  const files = Array.from(e.target.files || [])
  form.files = files
  if (files.length && !form.name) {
    const rel = files[0].webkitRelativePath || ''
    const folderName = rel ? rel.split('/')[0] : ''
    if (folderName) {
      form.name = folderName.length > 30 ? folderName.slice(0, 30) : folderName
    }
  }
}

function clearFiles() {
  form.files = []
  if (folderInput.value) folderInput.value.value = ''
}

async function submitUpload() {
  await uploadFormRef.value.validate()
  if (!form.files.length) {
    ElMessage.warning('请选择模型文件夹')
    return
  }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('name', form.name); fd.append('language', form.language)
    fd.append('version', wrapVersion(form.version)); fd.append('size', form.size)
    form.files.forEach((f) => fd.append('files', f, f.webkitRelativePath || f.name))
    await ModelAPI.create(fd)
    ElMessage.success('上传成功')
    uploadVisible.value = false
    Object.assign(form, { name: '', language: 'zh', version: '', size: 'base', files: [] })
    if (folderInput.value) folderInput.value.value = ''
    reload()
  } finally {
    submitting.value = false
  }
}

const editVisible = ref(false)
const editForm = reactive({ id: 0, name: '', version: '', language: 'zh', size: 'base' })
function openEdit(row) {
  Object.assign(editForm, {
    id: row.id,
    name: row.name,
    version: unwrapVersion(row.version),
    language: row.language,
    size: row.size
  })
  editVisible.value = true
}
async function submitEdit() {
  if (!/^\d+$/.test(String(editForm.version))) {
    ElMessage.warning('版本末尾只能是数字')
    return
  }
  await ModelAPI.update(editForm.id, {
    name: editForm.name,
    version: wrapVersion(editForm.version),
    language: editForm.language,
    size: editForm.size
  })
  ElMessage.success('修改成功')
  editVisible.value = false
  reload()
}

const detailVisible = ref(false)
const detail = ref({})
async function openDetail(row) {
  detail.value = await ModelAPI.detail(row.id)
  detailVisible.value = true
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确认删除模型「${row.name}」吗?`, '提示', { type: 'warning' })
  } catch { return }
  await ModelAPI.remove(row.id)
  ElMessage.success('已删除')
  reload()
}

const remoteVisible = ref(false)
const remoteLoading = ref(false)
const remoteBaseUrl = ref('')
const remoteForm = reactive({ languages: [], sizes: [], versions: [] })
const remoteCatalog = ref({ items: [], versions: [], errors: [] })
const remoteResults = ref([])

const remoteVersionOptions = computed(() => remoteCatalog.value.versions || [])

const remoteDownloadCount = computed(() => {
  if (!remoteForm.languages.length || !remoteForm.sizes.length || !remoteForm.versions.length) return 0
  return remoteForm.languages.length * remoteForm.sizes.length * remoteForm.versions.length
})

const isRemoteJobActive = computed(() => activeJob.value?.status === 'running')

const showDownloadBanner = computed(() => isRemoteJobActive.value)

const downloadPercent = computed(() => {
  const p = Number(activeJob.value?.percent ?? 0)
  return Math.min(100, Math.max(0, Math.round(p)))
})

const downloadProgressText = computed(() => {
  const job = activeJob.value
  if (!job) return ''
  const parts = []
  if (job.total_items) {
    parts.push(`第 ${job.current_item_index || 0}/${job.total_items} 个`)
  }
  if (job.phase_label) parts.push(job.phase_label)
  else if (job.message) parts.push(job.message)
  return parts.join(' · ') || '处理中…'
})

const downloadBytesText = computed(() => {
  const job = activeJob.value
  if (!job?.total_bytes) return ''
  return `${formatSize(job.downloaded_bytes)} / ${formatSize(job.total_bytes)}`
})

const remotePreviewItems = computed(() => {
  const langs = new Set(remoteForm.languages)
  const sizes = new Set(remoteForm.sizes)
  const vers = new Set(remoteForm.versions)
  return (remoteCatalog.value.items || []).filter(
    (item) => langs.has(item.language) && sizes.has(item.size) && vers.has(item.version)
  )
})

async function openRemoteDownload() {
  if (!isRemoteJobActive.value) {
    remoteResults.value = []
    Object.assign(remoteForm, { languages: [], sizes: [], versions: [] })
    remoteCatalog.value = { items: [], versions: [], errors: [] }
  } else {
    syncRemoteResultsFromJob(activeJob.value)
  }
  remoteVisible.value = true
  try {
    const cfg = await ModelAPI.remoteConfig()
    remoteBaseUrl.value = cfg.base_url || ''
  } catch {
    remoteBaseUrl.value = ''
  }
}

function syncRemoteResultsFromJob(job) {
  if (job?.results?.length) {
    remoteResults.value = job.results
  }
}

function resetRemoteForm() {
  if (activeJob.value?.status === 'running') return
  remoteResults.value = []
  Object.assign(remoteForm, { languages: [], sizes: [], versions: [] })
  remoteCatalog.value = { items: [], versions: [], errors: [] }
}

function onRemoteDialogClosed() {
  resetRemoteForm()
}

async function onCancelRemoteDownload() {
  try {
    await ElMessageBox.confirm('确定要取消正在进行的下载吗？', '取消下载', { type: 'warning' })
  } catch {
    return
  }
  await cancelDownload()
  remoteVisible.value = false
}

async function loadRemoteCatalog() {
  if (!remoteForm.languages.length || !remoteForm.sizes.length) {
    remoteCatalog.value = { items: [], versions: [], errors: [] }
    remoteForm.versions = []
    return
  }
  remoteLoading.value = true
  try {
    const data = await ModelAPI.remoteCatalog({
      language: remoteForm.languages,
      size: remoteForm.sizes
    })
    remoteCatalog.value = data
    const allowed = new Set(data.versions || [])
    remoteForm.versions = remoteForm.versions.filter((v) => allowed.has(v))
  } finally {
    remoteLoading.value = false
  }
}

watch(
  () => [remoteForm.languages.slice(), remoteForm.sizes.slice()],
  () => {
    if (!remoteVisible.value) return
    loadRemoteCatalog()
  }
)

async function submitRemoteDownload() {
  if (!remoteForm.languages.length || !remoteForm.sizes.length || !remoteForm.versions.length) {
    ElMessage.warning('请选择语种、尺寸和版本')
    return
  }
  if (!remoteBaseUrl.value) {
    ElMessage.warning('未配置远程下载地址')
    return
  }
  if (isRemoteJobActive.value) {
    ElMessage.warning('已有下载任务进行中')
    return
  }
  remoteResults.value = []
  try {
    await startDownload(
      {
        languages: remoteForm.languages,
        sizes: remoteForm.sizes,
        versions: remoteForm.versions
      },
      {
        onDone: (data) => {
          syncRemoteResultsFromJob(data)
          if (data?.ok > 0) reload()
        }
      }
    )
    ElMessage.info('下载已在后台进行，可关闭窗口，进度将显示在页面顶部')
  } catch {
    /* http 拦截器已提示 */
  }
}

watch(activeJob, (job) => {
  if (job?.results?.length) {
    remoteResults.value = job.results
  }
})
</script>

<style scoped>
.download-banner {
  margin-bottom: 12px;
}
.download-banner-sub {
  margin-left: 8px;
  font-weight: normal;
  color: #606266;
}
.download-banner-body {
  margin-top: 8px;
}
.download-banner-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
  flex-wrap: wrap;
}
</style>
