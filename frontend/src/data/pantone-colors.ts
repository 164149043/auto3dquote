/**
 * 常用颜色色板 — 用于喷漆颜色选择
 * 包含基础色、工业常用色、金属色
 */

export interface ColorSwatch {
  hex: string
  nameZh: string
  nameEn: string
  pantoneCode?: string
  category: 'basic' | 'industrial' | 'metallic'
}

export const COLOR_PALETTE: ColorSwatch[] = [
  // 基础色
  { hex: '#FFFFFF', nameZh: '白色', nameEn: 'White', category: 'basic' },
  { hex: '#000000', nameZh: '黑色', nameEn: 'Black', category: 'basic' },
  { hex: '#808080', nameZh: '灰色', nameEn: 'Gray', category: 'basic' },
  { hex: '#C0C0C0', nameZh: '银灰', nameEn: 'Silver Gray', category: 'basic' },
  { hex: '#FF0000', nameZh: '红色', nameEn: 'Red', category: 'basic' },
  { hex: '#FF4500', nameZh: '橙红', nameEn: 'Orange Red', category: 'basic' },
  { hex: '#FFA500', nameZh: '橙色', nameEn: 'Orange', category: 'basic' },
  { hex: '#FFFF00', nameZh: '黄色', nameEn: 'Yellow', category: 'basic' },
  { hex: '#00FF00', nameZh: '绿色', nameEn: 'Green', category: 'basic' },
  { hex: '#008000', nameZh: '深绿', nameEn: 'Dark Green', category: 'basic' },
  { hex: '#0000FF', nameZh: '蓝色', nameEn: 'Blue', category: 'basic' },
  { hex: '#000080', nameZh: '深蓝', nameEn: 'Navy', category: 'basic' },
  { hex: '#800080', nameZh: '紫色', nameEn: 'Purple', category: 'basic' },
  { hex: '#FFC0CB', nameZh: '粉色', nameEn: 'Pink', category: 'basic' },
  { hex: '#8B4513', nameZh: '棕色', nameEn: 'Brown', category: 'basic' },
  // 工业常用色
  { hex: '#1B3A4B', nameZh: '工业蓝', nameEn: 'Industrial Blue', category: 'industrial' },
  { hex: '#2E4057', nameZh: '工程灰蓝', nameEn: 'Engineering Blue', category: 'industrial' },
  { hex: '#048A81', nameZh: '青绿', nameEn: 'Teal', category: 'industrial' },
  { hex: '#3D5A80', nameZh: '暗蓝', nameEn: 'Dark Blue', category: 'industrial' },
  { hex: '#EE6C4D', nameZh: '珊瑚橙', nameEn: 'Coral', category: 'industrial' },
  { hex: '#F4845F', nameZh: '鲑鱼粉', nameEn: 'Salmon', category: 'industrial' },
  { hex: '#2A9D8F', nameZh: '蒂芙尼绿', nameEn: 'Tiffany Green', category: 'industrial' },
  { hex: '#E76F51', nameZh: '赤陶', nameEn: 'Terracotta', category: 'industrial' },
  { hex: '#264653', nameZh: '暗青', nameEn: 'Charcoal Teal', category: 'industrial' },
  { hex: '#E9C46A', nameZh: '芥末黄', nameEn: 'Mustard', category: 'industrial' },
  { hex: '#F4A261', nameZh: '沙橙', nameEn: 'Sandy Orange', category: 'industrial' },
  { hex: '#606C38', nameZh: '橄榄绿', nameEn: 'Olive', category: 'industrial' },
  // 金属色
  { hex: '#D4AF37', nameZh: '金色', nameEn: 'Gold', category: 'metallic' },
  { hex: '#C5A028', nameZh: '暗金', nameEn: 'Dark Gold', category: 'metallic' },
  { hex: '#B87333', nameZh: '铜色', nameEn: 'Copper', category: 'metallic' },
  { hex: '#954535', nameZh: '青铜', nameEn: 'Bronze', category: 'metallic' },
  { hex: '#E8E8E8', nameZh: '亮银', nameEn: 'Bright Silver', category: 'metallic' },
  { hex: '#A8A9AD', nameZh: '哑光银', nameEn: 'Matte Silver', category: 'metallic' },
  { hex: '#507D2A', nameZh: '军绿', nameEn: 'Army Green', category: 'metallic' },
  { hex: '#353839', nameZh: '枪灰', nameEn: 'Gunmetal', category: 'metallic' },
]
