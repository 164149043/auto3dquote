/**
 * Admin API 调用封装
 */

const API_BASE = '/api/v1/admin'

let _token = localStorage.getItem('admin_token') || ''

function headers(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${_token}`,
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers: headers() })
  if (res.status === 401) throw new Error('认证失败，请重新输入 Token')
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `请求失败 (${res.status})`)
  }
  return res.json()
}

export function useAdminApi() {
  function setToken(token: string) {
    _token = token
    localStorage.setItem('admin_token', token)
  }

  function clearToken() {
    _token = ''
    localStorage.removeItem('admin_token')
  }

  function getToken(): string {
    return _token
  }

  // 完整配置快照
  async function getConfig() {
    return request<Record<string, unknown>>('/config')
  }

  // 材料 CRUD
  async function listMaterials() {
    return request<Array<Record<string, unknown>>>('/materials')
  }

  async function createMaterial(data: Record<string, unknown>) {
    return request<{ ok: boolean; id: string }>('/materials', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async function updateMaterial(id: string, data: Record<string, unknown>) {
    return request<{ ok: boolean }>(`/materials/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async function deleteMaterial(id: string) {
    return request<{ ok: boolean }>(`/materials/${id}`, { method: 'DELETE' })
  }

  async function uploadMaterialImage(id: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API_BASE}/materials/${id}/image`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${_token}` },
      body: formData,
    })
    if (res.status === 401) throw new Error('认证失败')
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `上传失败 (${res.status})`)
    }
    return res.json() as Promise<{ ok: boolean; image_url: string }>
  }

  // 后处理 CRUD
  async function listPostProcesses() {
    return request<Array<Record<string, unknown>>>('/post-processes')
  }

  async function createPostProcess(data: Record<string, unknown>) {
    return request<{ ok: boolean; id: string }>('/post-processes', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async function updatePostProcess(id: string, data: Record<string, unknown>) {
    return request<{ ok: boolean }>(`/post-processes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async function deletePostProcess(id: string) {
    return request<{ ok: boolean }>(`/post-processes/${id}`, { method: 'DELETE' })
  }

  // 交期选项
  async function listDeliveryOptions() {
    return request<Array<Record<string, unknown>>>('/delivery-options')
  }

  async function updateDeliveryOption(id: string, data: Record<string, unknown>) {
    return request<{ ok: boolean }>(`/delivery-options/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // 工艺映射
  async function getProcessMapping() {
    return request<Record<string, unknown>>('/process-mapping')
  }

  async function updateProcessMaterials(processId: string, materialIds: string[]) {
    return request<{ ok: boolean }>(`/process-mapping/${processId}/materials`, {
      method: 'PUT',
      body: JSON.stringify({ material_ids: materialIds }),
    })
  }

  async function updateProcessPostProcesses(processId: string, postProcessIds: string[]) {
    return request<{ ok: boolean }>(`/process-mapping/${processId}/post-processes`, {
      method: 'PUT',
      body: JSON.stringify({ post_process_ids: postProcessIds }),
    })
  }

  // 设备体积限制
  async function listMachineLimits() {
    return request<Array<Record<string, unknown>>>('/machine-limits')
  }

  async function updateMachineLimits(processId: string, data: { max_x: number; max_y: number; max_z: number }) {
    return request<{ ok: boolean }>(`/machine-limits/${processId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // 全局设置
  async function listSettings() {
    return request<Array<Record<string, unknown>>>('/settings')
  }

  async function updateSetting(key: string, value: unknown, description?: string) {
    return request<{ ok: boolean }>(`/settings/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value: JSON.stringify(value), description }),
    })
  }

  // 缓存刷新
  async function refreshCache() {
    return request<{ ok: boolean; message: string }>('/cache/refresh', { method: 'POST' })
  }

  return {
    setToken,
    clearToken,
    getToken,
    getConfig,
    listMaterials,
    createMaterial,
    updateMaterial,
    deleteMaterial,
    uploadMaterialImage,
    listPostProcesses,
    createPostProcess,
    updatePostProcess,
    deletePostProcess,
    listDeliveryOptions,
    updateDeliveryOption,
    getProcessMapping,
    updateProcessMaterials,
    updateProcessPostProcesses,
    listMachineLimits,
    updateMachineLimits,
    listSettings,
    updateSetting,
    refreshCache,
  }
}
