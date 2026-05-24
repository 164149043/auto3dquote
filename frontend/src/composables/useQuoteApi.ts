/**
 * API 调用封装
 */

import type {
  QuoteResponse,
  OptionsResponse,
  QuoteParams,
  QuoteRecordListResponse,
  QuoteRecordDetail,
} from '../types/api'

const API_BASE = '/api/v1'

function getAuthHeaders(): Record<string, string> {
  const t = localStorage.getItem('user_token') || ''
  return t ? { Authorization: `Bearer ${t}` } : {}
}

export function useQuoteApi() {
  async function submitQuote(file: File, params: QuoteParams): Promise<QuoteResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('process', params.process)
    formData.append('material', params.material)
    formData.append('quality', params.quality)
    formData.append('quantity', String(params.quantity))
    formData.append('post_processing', params.post_processing.join(','))
    formData.append('delivery', params.delivery)
    if (params.paint_options) {
      formData.append('paint_options', JSON.stringify({
        finish: params.paint_options.finishType,
        color: params.paint_options.color,
      }))
    }

    const headers: Record<string, string> = getAuthHeaders()
    const response = await fetch(`${API_BASE}/quote`, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (response.status === 401) {
      localStorage.removeItem('user_token')
      throw new Error('登录已过期，请重新登录')
    }

    if (!response.ok) {
      let msg = `请求失败 (${response.status})`
      try {
        const data = await response.json()
        if (data.message) msg = data.message
        else if (Array.isArray(data.detail)) msg = data.detail.map((d: any) => d.msg).join('; ')
        else if (typeof data.detail === 'string') msg = data.detail
      } catch { /* JSON 解析失败，用默认消息 */ }
      throw new Error(msg)
    }

    return response.json()
  }

  async function fetchOptions(): Promise<OptionsResponse> {
    const response = await fetch(`${API_BASE}/materials`)
    if (!response.ok) throw new Error('获取选项列表失败')
    return response.json()
  }

  async function healthCheck(): Promise<{ status: string; prusa_slicer_available: boolean }> {
    const response = await fetch(`${API_BASE}/health`)
    return response.json()
  }

  async function convertToStl(file: File): Promise<Blob> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/convert`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || `转换失败 (${response.status})`)
    }

    return response.blob()
  }

  // ==================== 报价历史 ====================

  async function fetchQuoteRecords(page = 1, pageSize = 10): Promise<QuoteRecordListResponse> {
    const res = await fetch(`${API_BASE}/auth/quotes?page=${page}&page_size=${pageSize}`, {
      headers: getAuthHeaders(),
    })
    if (!res.ok) throw new Error('获取报价记录失败')
    return res.json()
  }

  async function fetchQuoteRecordDetail(id: number): Promise<QuoteRecordDetail> {
    const res = await fetch(`${API_BASE}/auth/quotes/${id}`, {
      headers: getAuthHeaders(),
    })
    if (!res.ok) throw new Error('获取报价详情失败')
    return res.json()
  }

  async function deleteQuoteRecord(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/auth/quotes/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    if (!res.ok) throw new Error('删除失败')
  }

  return {
    submitQuote,
    fetchOptions,
    healthCheck,
    convertToStl,
    fetchQuoteRecords,
    fetchQuoteRecordDetail,
    deleteQuoteRecord,
  }
}
