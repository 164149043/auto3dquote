/**
 * 材料分类定义
 */

export interface MaterialCategory {
  id: string
  labelZh: string
  labelEn: string
}

export const MATERIAL_CATEGORIES: MaterialCategory[] = [
  { id: 'resin', labelZh: '树脂', labelEn: 'Resin' },
  { id: 'nylon', labelZh: '尼龙', labelEn: 'Nylon' },
  { id: 'engineering_resin', labelZh: '工程树脂', labelEn: 'Engineering Resin' },
  { id: 'metal', labelZh: '金属', labelEn: 'Metal' },
  { id: 'high_perf', labelZh: '高性能材料', labelEn: 'High Performance' },
  { id: 'other', labelZh: '其他', labelEn: 'Other' },
]
