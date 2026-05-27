/** 各算法模块路由 meta 约定，便于 MT / TTS 等复用同一套面包屑与返回逻辑 */

export const MODULES = {
  asr: { prefix: 'ASR', tasksPath: '/asr/tasks', tasksTitle: 'ASR · 测试任务' },
  mt: { prefix: 'MT', tasksPath: '/mt/tasks', tasksTitle: 'MT · 测试任务' },
  tts: { prefix: 'TTS', tasksPath: '/tts/tasks', tasksTitle: 'TTS · 测试任务' }
}

/** 列表页 meta */
export function listPageMeta(module, pageTitle) {
  const m = MODULES[module]
  return { title: pageTitle || m.tasksTitle }
}

/** 任务结果详情页 meta：面包屑 + 返回按钮配置 */
export function taskResultMeta(module) {
  const m = MODULES[module]
  return {
    title: `${m.prefix} · 结果详情`,
    breadcrumbs: [{ title: m.tasksTitle, path: m.tasksPath }],
    back: { path: m.tasksPath, label: '返回测试任务' }
  }
}
