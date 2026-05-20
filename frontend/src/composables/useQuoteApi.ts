/**
 * API 调用封装
 */

import type { QuoteResponse, OptionsResponse, QuoteParams } from '../types/api'

const API_BASE = '/api/v1'

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

    const response = await fetch(`${API_BASE}/quote`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      let msg = `请求失败 (${response.status})`
      try {
        const data = await response.json()
        // 业务错误: { message: "..." }
        if (data.message) msg = data.message
        // FastAPI 422 校验错误: { detail: [{ msg: "..." }] }
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

  return { submitQuote, fetchOptions, healthCheck, convertToStl }
}
