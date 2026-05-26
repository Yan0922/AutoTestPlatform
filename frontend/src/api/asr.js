import http from './http'

export const ModelAPI = {
  list: (params) => http.get('/asr/models/', { params }),
  detail: (id) => http.get(`/asr/models/${id}/`),
  remove: (id) => http.delete(`/asr/models/${id}/`),
  update: (id, data) => http.put(`/asr/models/${id}/`, data),
  create: (formData) => http.post('/asr/models/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  remoteConfig: () => http.get('/asr/models/remote-config/'),
  remoteCatalog: (params) => http.get('/asr/models/remote-catalog/', { params }),
  remoteDownloadStart: (data) => http.post('/asr/models/remote-download/start/', data),
  remoteDownloadStatus: (jobId) => http.get('/asr/models/remote-download/status/', {
    params: jobId ? { job_id: jobId } : {}
  }),
  remoteDownloadCancel: (jobId) => http.post('/asr/models/remote-download/cancel/', { job_id: jobId })
}

export const DatasetAPI = {
  list: (params) => http.get('/asr/datasets/', { params }),
  create: (data) => http.post('/asr/datasets/', data),
  update: (id, data) => http.put(`/asr/datasets/${id}/`, data),
  remove: (id) => http.delete(`/asr/datasets/${id}/`),
  removeAudios: (id, audio_ids) => http.post(`/asr/datasets/${id}/remove-audios/`, { audio_ids })
}

export const AudioAPI = {
  list: (params) => http.get('/asr/audios/', { params }),
  remove: (id) => http.delete(`/asr/audios/${id}/`),
  batchDelete: (ids) => http.post('/asr/audios/batch-delete/', { ids }),
  joinDataset: (audio_ids, dataset_ids) => http.post('/asr/audios/join-dataset/', { audio_ids, dataset_ids }),
  updateText: (id, ref_text) => http.patch(`/asr/audios/${id}/update-text/`, { ref_text }),
  updateInfo: (id, data) => http.patch(`/asr/audios/${id}/update-info/`, data),
  templateUrl: '/api/asr/audios/template/',
  parseExcel: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post('/asr/audios/parse-excel/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  import: (rows) => http.post('/asr/audios/import/', { rows })
}

export const TaskAPI = {
  list: (params) => http.get('/asr/tasks/', { params }),
  create: (data) => http.post('/asr/tasks/', data),
  result: (id, params) => http.get(`/asr/tasks/${id}/result/`, { params }),
  remove: (id) => http.delete(`/asr/tasks/${id}/`)
}
