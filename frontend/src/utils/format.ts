/**
 * 格式化工具函数
 */

export function formatPrice(value: number): string {
  return `¥${value.toFixed(2)}`
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function formatDimensions(dim: { x_mm: number; y_mm: number; z_mm: number }): string {
  return `${dim.x_mm.toFixed(2)} × ${dim.y_mm.toFixed(2)} × ${dim.z_mm.toFixed(2)} mm`
}
