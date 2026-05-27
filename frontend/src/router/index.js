import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/views/Layout.vue'
import { listPageMeta, taskResultMeta } from './meta'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/asr/models',
    children: [
      { path: 'asr/models', name: 'asr-models', component: () => import('@/views/asr/ModelList.vue'), meta: { title: 'ASR · 模型管理' } },
      { path: 'asr/datasets', name: 'asr-datasets', component: () => import('@/views/asr/DatasetList.vue'), meta: { title: 'ASR · 数据集管理' } },
      { path: 'asr/pool', name: 'asr-pool', component: () => import('@/views/asr/DataPool.vue'), meta: { title: 'ASR · 数据池' } },
      { path: 'asr/tasks', name: 'asr-tasks', component: () => import('@/views/asr/TaskList.vue'), meta: listPageMeta('asr') },
      { path: 'asr/tasks/:id/result', name: 'asr-task-result', component: () => import('@/views/asr/TaskResult.vue'), meta: taskResultMeta('asr') },
      { path: 'mt', name: 'mt', component: () => import('@/views/placeholder/Placeholder.vue'), meta: { title: 'MT' } },
      { path: 'tts', name: 'tts', component: () => import('@/views/placeholder/Placeholder.vue'), meta: { title: 'TTS' } }
      // MT / TTS 接入结果页时示例：
      // { path: 'mt/tasks', meta: listPageMeta('mt') },
      // { path: 'mt/tasks/:id/result', meta: taskResultMeta('mt') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
