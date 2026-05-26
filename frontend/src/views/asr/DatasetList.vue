<template>
  <div class="page-card sticky-page">
    <div class="toolbar sticky-toolbar">
      <el-input v-model="search" placeholder="按数据集名称搜索" clearable style="width:240px;" @change="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button type="success" @click="openCreate">新增数据集</el-button>
    </div>

    <div class="sticky-body">
    <el-row :gutter="12">
      <!-- 左侧 数据集列表 -->
      <el-col :span="10" class="sticky-col">
        <div ref="dsTableWrapRef" class="sticky-table-wrap">
        <el-table
          :data="rows" border stripe v-loading="loadingDs"
          :height="dsTableHeight"
          highlight-current-row @current-change="onSelectDataset"
        >
          <el-table-column prop="name" label="数据集名称" min-width="120" />
          <el-table-column prop="language_display" label="语种" width="70" />
          <el-table-column prop="total_audio" label="音频数" width="80" />
          <el-table-column label="总时长" width="110">
            <template #default="{ row }">{{ formatDuration(row.total_duration) }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click.stop="openEdit(row)">修改</el-button>
              <el-button size="small" type="danger" @click.stop="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        </div>
        <div class="pager sticky-pager">
          <el-pagination background layout="prev, pager, next, total"
            :total="total" :page-size="10" :current-page="page" @current-change="onPage" />
        </div>
      </el-col>

      <!-- 右侧 当前数据集音频列表 -->
      <el-col :span="14" class="sticky-col">
        <div v-if="!currentDataset" class="sticky-empty">请在左侧选择一个数据集查看音频</div>
        <template v-else>
          <div class="toolbar sticky-toolbar">
            <strong>当前数据集: {{ currentDataset.name }}</strong>
            <el-button size="small" type="danger" :disabled="!selectedAudios.length" @click="batchRemoveAudios">移除选中音频</el-button>
          </div>
          <div ref="audioTableWrapRef" class="sticky-table-wrap">
          <el-table
            :data="audios" border stripe v-loading="loadingAudio"
            :height="audioTableHeight"
            @selection-change="(rows) => selectedAudios = rows"
          >
            <el-table-column type="selection" width="46" />
            <el-table-column prop="name" label="音频名称" min-width="160" />
            <el-table-column label="播放" width="220">
              <template #default="{ row }">
                <audio :src="row.audio_path" controls preload="metadata" style="height:32px;width:100%;" />
              </template>
            </el-table-column>
            <el-table-column label="时长" width="100">
              <template #default="{ row }">{{ formatDuration(row.duration) }}</template>
            </el-table-column>
            <el-table-column label="文本" min-width="200">
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
          </el-table>
          </div>
          <div class="pager sticky-pager">
            <el-pagination background layout="prev, pager, next, total"
              :total="audioTotal" :page-size="50" :current-page="audioPage" @current-change="onAudioPage" />
          </div>
        </template>
      </el-col>
    </el-row>
    </div>

    <!-- 新增/修改弹窗 -->
    <el-dialog v-model="dsDialog.visible" :title="dsDialog.id ? '修改数据集' : '新增数据集'" width="420px">
      <el-form :model="dsDialog" label-width="100px">
        <el-form-item label="数据集名称" required>
          <el-input v-model="dsDialog.name" maxlength="30" show-word-limit />
        </el-form-item>
        <el-form-item v-if="!dsDialog.id" label="语种">
          <el-select v-model="dsDialog.language">
            <el-option v-for="l in LANGUAGES" :key="l.value" :label="l.label" :value="l.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dsDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitDataset">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { AudioAPI, DatasetAPI } from '@/api/asr'
import { formatDuration } from '@/utils/format'
import { useStickyTable } from '@/composables/useStickyTable'

const LANGUAGES = [
  { value: 'zh', label: '中' }, { value: 'en', label: '英' }, { value: 'es', label: '西' },
  { value: 'ja', label: '日' }, { value: 'ko', label: '韩' }, { value: 'ru', label: '俄' },
  { value: 'fr', label: '法' }, { value: 'de', label: '德' }, { value: 'th', label: '泰' },
  { value: 'it', label: '意' }, { value: 'ar', label: '阿' }
]

const rows = ref([])
const total = ref(0)
const page = ref(1)
const loadingDs = ref(false)
const search = ref('')
const { tableWrapRef: dsTableWrapRef, tableHeight: dsTableHeight, updateTableHeight: updateDsTableHeight } = useStickyTable()
const { tableWrapRef: audioTableWrapRef, tableHeight: audioTableHeight, updateTableHeight: updateAudioTableHeight } = useStickyTable()

async function reload() {
  loadingDs.value = true
  try {
    const data = await DatasetAPI.list({ search: search.value, page: page.value, page_size: 10 })
    rows.value = data.results || []
    total.value = data.count || 0
  } finally {
    loadingDs.value = false
    updateDsTableHeight()
  }
}
function onPage(p) { page.value = p; reload() }
onMounted(reload)

const dsDialog = reactive({ visible: false, id: 0, name: '', language: 'zh' })
function openCreate() {
  Object.assign(dsDialog, { visible: true, id: 0, name: '', language: 'zh' })
}
function openEdit(row) {
  Object.assign(dsDialog, { visible: true, id: row.id, name: row.name, language: row.language })
}
async function submitDataset() {
  if (!dsDialog.name) { ElMessage.warning('请输入数据集名称'); return }
  if (dsDialog.id) {
    await DatasetAPI.update(dsDialog.id, { name: dsDialog.name, language: dsDialog.language })
    ElMessage.success('修改成功')
  } else {
    await DatasetAPI.create({ name: dsDialog.name, language: dsDialog.language })
    ElMessage.success('新增成功')
  }
  dsDialog.visible = false
  reload()
}
async function remove(row) {
  try {
    await ElMessageBox.confirm('当前删除操作会一并解除数据集中音频关系，确定删除吗?', '提示', { type: 'warning' })
  } catch { return }
  await DatasetAPI.remove(row.id)
  ElMessage.success('已删除')
  if (currentDataset.value?.id === row.id) currentDataset.value = null
  reload()
}

// 右侧 音频
const currentDataset = ref(null)
const audios = ref([])
const audioTotal = ref(0)
const audioPage = ref(1)
const selectedAudios = ref([])
const loadingAudio = ref(false)

async function onSelectDataset(row) {
  currentDataset.value = row
  audioPage.value = 1
  await loadAudios()
  await nextTick()
  updateAudioTableHeight()
}
async function loadAudios() {
  if (!currentDataset.value) return
  loadingAudio.value = true
  try {
    const data = await AudioAPI.list({
      dataset_id: currentDataset.value.id, page: audioPage.value, page_size: 50
    })
    audios.value = data.results || []
    audioTotal.value = data.count || 0
  } finally {
    loadingAudio.value = false
    updateAudioTableHeight()
  }
}
function onAudioPage(p) { audioPage.value = p; loadAudios() }

async function batchRemoveAudios() {
  try {
    await ElMessageBox.confirm(`确认将选中的 ${selectedAudios.value.length} 个音频从数据集中移除?`, '提示', { type: 'warning' })
  } catch { return }
  await DatasetAPI.removeAudios(currentDataset.value.id, selectedAudios.value.map(r => r.id))
  ElMessage.success('已移除')
  loadAudios()
  reload()
}

// 文本编辑
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
</script>
