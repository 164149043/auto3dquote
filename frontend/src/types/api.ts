/**
 * 与后端 Pydantic 模型一一对应的 TypeScript 类型定义
 */

export interface MeshDimensions {
  x_mm: number
  y_mm: number
  z_mm: number
}

export interface MeshAnalysisResult {
  is_watertight: boolean
  volume_mm3: number
  bounding_box: MeshDimensions
  surface_area_mm2: number
  triangle_count: number
  vertex_count: number
  file_size_bytes: number
  warnings: string[]
}

export interface SlicingResult {
  print_time_seconds: number
  print_time_formatted: string
  filament_used_mm: number
  filament_used_grams: number
  filament_used_cm3: number
  layer_count: number
  gcode_file_size_bytes: number
  slicer_version: string
}

export interface MaterialCost {
  material_type: string
  unit_price: number
  quantity: number
  unit: string
  subtotal: number
}

export interface TimeCost {
  rate_per_hour: number
  hours: number
  subtotal: number
}

export interface PostProcessCost {
  name: string
  type: string
  unit_price: number
  subtotal: number
}

export interface CostBreakdown {
  material_cost: MaterialCost
  time_cost: TimeCost
  post_process_costs: PostProcessCost[]
  delivery_surcharge: number
  difficulty_score: number
  difficulty_multiplier: number
  difficulty_surcharge: number
  support_weight: number
  support_cost: number
  quantity_discount: number
  quantity_discount_rate: number
  base_price: number
  markup_rate: number
  unit_price: number
  quantity: number
  total_price: number
}

export interface QuoteResponse {
  status: 'success' | 'warning' | 'partial'
  analysis: MeshAnalysisResult
  slicing: SlicingResult | null
  quote: CostBreakdown | null
  warnings: string[]
  processing_time_seconds: number
  timestamp: string
}

// ==================== 选项树类型 ====================

export interface MaterialOption {
  id: string
  label: string
  price: number
  unit: string
  category?: string
  image_url?: string
  description?: string
}

export interface QualityOption {
  id: string
  label: string
  desc: string
}

export interface PostProcessOption {
  id: string
  label: string
  price_mode: 'fixed' | 'percentage'
  price_value: number
  description?: string
}

export interface DeliveryOption {
  id: string
  label: string
  surcharge: number
  days?: number
}

export interface ProcessOption {
  id: string
  label: string
  materials: MaterialOption[]
  quality_options: QualityOption[]
  post_processes: PostProcessOption[]
  delivery_options: DeliveryOption[]
}

export interface OptionsResponse {
  currency: string
  time_cost_per_hour: number
  markup_rate: number
  processes: ProcessOption[]
}

export interface ErrorResponse {
  error: string
  message: string
  detail: string | null
  timestamp: string
}

export interface PaintConfig {
  finishType: 'matte' | 'glossy'
  color: string
  colorName?: string
}

export interface QuoteParams {
  process: string
  material: string
  quality: string
  quantity: number
  post_processing: string[]
  delivery: string
  paint_options?: PaintConfig | null
}

// ==================== 用户认证类型 ====================

export interface UserResponse {
  id: number
  username: string
  role: string
  is_active: number
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

export interface CaptchaResponse {
  captcha_id: string
  captcha_image: string
}

// ==================== 报价记录类型 ====================

export interface QuoteRecordItem {
  id: number
  filename: string
  process: string
  material: string
  quantity: number
  status: string
  unit_price: number
  total_price: number
  created_at: string
}

export interface QuoteRecordDetail extends QuoteRecordItem {
  quality: string
  delivery: string
  post_processing: string | null
  material_cost: number
  time_cost: number
  post_process_cost: number
  delivery_surcharge: number
  difficulty_surcharge: number
  support_cost: number
  quantity_discount: number
  volume_mm3: number
  surface_area_mm2: number
  bounding_box: string | null
  file_size_bytes: number | null
  print_time_seconds: number | null
  filament_used_grams: number | null
  processing_time_seconds: number
}

export interface QuoteRecordListResponse {
  total: number
  page: number
  page_size: number
  records: QuoteRecordItem[]
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  confirm_password: string
}
