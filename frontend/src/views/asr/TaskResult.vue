<template>
  <div class="page-card sticky-page">
    <div class="sticky-toolbar" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
      <div>
        <h3 style="margin:0 0 6px;">{{ taskInfo?.name }}</h3>
        <span style="color:#909399;">模型: {{ taskInfo?.model_name }} | 创建: {{ taskInfo?.created_at }} | 完成: {{ taskInfo?.finished_at || '-' }}</span>
      </div>
    </div>

    <div class="sticky-body" v-loading="loading">
    <el-row :gutter="12">
      <!-- 左侧 数据集卡片 -->
      <el-col :span="8" class="sticky-col-scroll">
        <div v-for="d in datasets" :key="d.id"
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
      </el-col>

      <!-- 右侧 音频结果列表 -->
      <el-col :span="16" class="sticky-col">
        <div ref="tableWrapRef" class="sticky-table-wrap">
        <el-table :data="results" border stripe :height="tableHeight">
          <el-table-column prop="audio_name" label="音频名称" min-width="160" />
          <el-table-column label="播放" width="220">
            <template #default="{ row }">
              <audio :src="row.audio_path" controls preload="metadata" style="height:32px;width:100%;" />
            </template>
          </el-table-column>
          <el-table-column label="WER" width="90">
            <template #default="{ row }">{{ (row.wer * 100).toFixed(2) }}%</template>
          </el-table-column>
          <el-table-column label="Ref" min-width="240">
            <template #default="{ row }">
              <div v-if="editingId !== row.id" @click="startEdit(row)" style="cursor:text;white-space:pre-wrap;">
                {{ row.ref_text }}
              </div>
              <div v-else>
                <el-input v-model="editingText" type="textarea" :rows="3" @blur="cancelEdit" />
                <el-button size="small" type="primary" style="margin-top:4px;" @mousedown.prevent="confirmEdit(row)">OK</el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="预测" min-width="260">
            <template #default="{ row }">
              <span v-for="(op, idx) in row.errors_json?.ops || []" :key="idx">
                <span v-if="op.op === 'H'">{{ op.hyp }}</span>
                <span v-else-if="op.op === 'S'" class="err-char" :title="`替换: ${op.ref}->${op.hyp}`">{{ op.hyp }}</span>
                <span v-else-if="op.op === 'I'" class="err-char" :title="`多识别: ${op.hyp}`">{{ op.hyp }}</span>
                <span v-else-if="op.op === 'D'" class="err-char" :title="`漏识别: ${op.ref}`">[漏]</span>
              </span>
            </template>
          </el-table-column>
        </el-table>
        </div>
      </el-col>
    </el-row>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'
import { AudioAPI, TaskAPI } from '@/api/asr'
import { formatDuration } from '@/utils/format'
import { useStickyTable } from '@/composables/useStickyTable'

const route = useRoute()
const taskId = Number(route.params.id)
const loading = ref(false)
const taskInfo = ref(null)
const datasets = ref([])
const results = ref([])
const currentDsId = ref(null)
const { tableWrapRef, tableHeight, updateTableHeight } = useStickyTable()

async function fetchData(dsId) {
  loading.value = true
  try {
    const data = await TaskAPI.result(taskId, dsId ? { dataset_id: dsId } : {})
    taskInfo.value = data.task
    datasets.value = data.datasets
    results.value = data.audio_results
    currentDsId.value = dsId || datasets.value[0]?.dataset
  } finally {
    loading.value = false
    updateTableHeight()
  }
}
function switchDataset(id) {
  fetchData(id)
}
onMounted(() => fetchData())

const editingId = ref(0)
const editingText = ref('')
function startEdit(row) { editingId.value = row.id; editingText.value = row.ref_text }
function cancelEdit() { editingId.value = 0 }
async function confirmEdit(row) {
  await AudioAPI.updateText(row.audio, editingText.value)
  row.ref_text = editingText.value
  editingId.value = 0
  ElMessage.success('已同步到数据池')
}
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
</style>
