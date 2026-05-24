# Auto3DQuote — 3D 打印自动报价系统

基于 PrusaSlicer 的 3D 打印自动报价平台。用户注册/登录后上传 3D 模型文件，系统自动分析模型几何信息、执行切片（FDM 工艺），并根据材料、时间、后处理、交期等参数实时计算报价。支持批量多文件上传、参数变更自动重新报价、历史报价记录查看和账号管理。

> **技术栈**：FastAPI + SQLAlchemy + Vue 3 + TypeScript + Three.js + TailwindCSS + PrusaSlicer CLI

---

## 目录

- [功能特性](#功能特性)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [报价计算原理](#报价计算原理)
  - [FDM 3D 打印](#1-fdm-3d-打印)
  - [SLA 光固化](#2-sla-光固化)
  - [SLS / MJF 粉末烧结](#3-sls--mjf-粉末烧结)
  - [CNC 数控加工](#4-cnc-数控加工)
  - [难度系数定价](#难度系数定价)
  - [支撑成本](#支撑成本)
  - [后处理费用](#后处理费用)
  - [交期加急费用](#交期加急费用)
  - [数量折扣](#数量折扣)
  - [最低起订价](#最低起订价)
  - [完整计算流程](#完整计算流程)
- [如何修改报价参数](#如何修改报价参数)
  - [通过管理后台（推荐）](#1-通过管理后台推荐)
  - [通过数据库直接修改](#2-通过数据库直接修改)
  - [通过 config.py 修改默认值](#3-通过-configpy-修改默认值)
  - [通过 .env 文件覆盖](#4-通过-env-文件覆盖)
- [支持的材料与工艺](#支持的材料与工艺)
- [API 接口](#api-接口)
- [用户系统](#用户系统)
- [管理后台](#管理后台)
- [数据库说明](#数据库说明)
- [后续计划](#后续计划)

---

## 功能特性

### 用户端

- **用户注册/登录**：支持用户名+密码注册（含图片验证码）和登录，JWT Token 认证，7天有效期
- **登录后报价**：必须登录后才能上传文件进行报价，未登录显示提示和登录按钮
- **批量上传报价**：支持同时上传多个文件（最多 10 个），每个文件独立配置参数、独立报价，底部显示合计总价
- **自动报价**：上传文件后自动触发报价，参数变更（材料、数量、表面处理、交期）后 500ms 防抖自动更新，无需手动点击
- **多工艺支持**：FDM / SLA / SLS / MJF / CNC 五种制造工艺，各有独立报价策略
- **19 种材料**：PLA、PETG、ABS、TPU、尼龙、标准/韧性/高温/柔性树脂、PA12/PA11/PA12+玻珠/TPU粉末、铝合金6061/7075、不锈钢304/316、黄铜、钛合金TC4
- **3D 模型预览**：基于 Three.js 的在线模型查看器，支持旋转/缩放/平移，带包围盒尺寸标注
- **紧凑报价卡片**：左右布局，左侧为 120×110px 缩略图预览（颜色随喷漆同步变化），右侧为文件名、尺寸、体积、参数面板、价格明细
- **材料选择弹窗**：分类浏览（树脂/尼龙/金属/其他）、材料卡片、详情面板（图片+介绍+价格）、确认选择
- **表面处理**：打磨、喷漆、抛光、阳极氧化、热处理等 11 种后处理，支持多选
- **喷漆子选项**：哑光/高光 + 潘通色板选择（~40种常用色 + 自定义颜色），缩略图颜色同步更新
- **交期选择**：标准(3天)、加急(2天)、特急(1天) 三档，默认加急(2天)
- **多数量报价**：支持 1-1000 件批量报价，含数量折扣
- **难度系数定价**：基于表面积/体积(SA/V)比自动识别薄壁件、精细件并加价
- **支撑成本**：基于几何特征估算 FDM 支撑材料重量并独立计费
- **价格明细展开**：点击"详情"展开完整的费用构成（材料、时间、支撑、难度、加急、后处理、折扣）
- **STEP 文件支持**：自动转换 STEP/STP 文件为 STL 进行预览和报价
- **报价历史**：查看所有历史报价记录，支持分页浏览、展开详情（完整成本明细和模型信息）、删除记录
- **账号管理**：修改密码功能，导航栏显示用户名和管理员标识

### 管理端

- **材料管理**：新增/编辑/删除材料，设置分类、单价、密度、图片、材料介绍
- **后处理管理**：新增/编辑/删除后处理选项，设置计费模式（固定/百分比）和价格
- **交期管理**：编辑各交期档位的加价系数和天数
- **工艺映射**：管理各工艺下可用的材料和后处理选项
- **设备限制**：设置各工艺的最大构建体积
- **全局设置**：结构化编辑基础费率、各工艺最低起订价、难度系数、支撑成本、数量折扣阶梯
- **材料图片上传**：为每种材料上传示例图片
- **配置热刷新**：修改配置后自动刷新缓存，API 实时返回最新数据

---

## 项目结构

```
Auto3DQuote/
├── backend/                          # 后端 (Python / FastAPI)
│   ├── app/
│   │   ├── main.py                   # 应用入口 + 静态文件挂载
│   │   ├── core/
│   │   │   ├── config.py             # 全局配置（默认值/环境变量）
│   │   │   ├── dependencies.py       # FastAPI 依赖注入（含 get_current_user）
│   │   │   ├── security.py           # JWT + 密码哈希
│   │   │   ├── captcha.py            # 验证码生成/校验/限流
│   │   │   └── exceptions.py         # 异常处理
│   │   ├── db/
│   │   │   ├── models.py             # SQLAlchemy 数据模型（含 User、QuoteRecord）
│   │   │   └── database.py           # 数据库引擎 + 种子数据 + 迁移
│   │   ├── models/
│   │   │   ├── common.py             # 枚举定义（工艺、材料、质量等）
│   │   │   ├── quote.py              # 报价数据模型 + 报价记录 Pydantic 模型
│   │   │   ├── auth.py               # 用户认证 Pydantic 模型
│   │   │   ├── analysis.py           # 网格分析结果模型
│   │   │   └── slicing.py            # 切片结果模型
│   │   ├── services/
│   │   │   ├── pipeline.py           # 主流程编排
│   │   │   ├── mesh_analyzer.py      # 网格分析（trimesh）
│   │   │   ├── slicer_service.py     # PrusaSlicer 调用
│   │   │   ├── gcode_parser.py       # G-code 解析
│   │   │   ├── file_service.py       # 文件上传/验证
│   │   │   ├── config_service.py     # 配置缓存服务（DB → 内存）
│   │   │   ├── quote_engine.py       # 遗留报价引擎（兼容）
│   │   │   └── pricing/              # 报价策略（策略模式）
│   │   │       ├── base.py           # 抽象基类
│   │   │       ├── fdm_strategy.py   # FDM 报价逻辑
│   │   │       ├── sla_strategy.py   # SLA/SLS/MJF 报价逻辑
│   │   │       ├── cnc_strategy.py   # CNC 报价逻辑
│   │   │       ├── utils.py          # 后处理/交期/折扣/最低价/难度/支撑计算
│   │   │       └── factory.py        # 策略工厂
│   │   ├── api/v1/endpoints/
│   │   │   ├── quote.py              # POST /api/v1/quote（需登录，自动保存记录）
│   │   │   ├── materials.py          # GET /api/v1/materials
│   │   │   ├── auth.py               # /api/v1/auth/* 用户认证 + 报价历史 + 修改密码
│   │   │   ├── admin.py              # /api/v1/admin/* 管理接口
│   │   │   ├── admin_auth.py         # Admin Token 认证
│   │   │   ├── convert.py            # POST /api/v1/convert (STEP→STL)
│   │   │   └── health.py             # GET /api/v1/health
│   │   └── utils/                    # 工具函数
│   ├── data/
│   │   ├── auto3dquote.db            # SQLite 数据库文件
│   │   └── material_images/          # 材料图片存储
│   ├── slicer_profiles/              # PrusaSlicer 配置文件
│   ├── .env.example                  # 环境变量示例
│   └── requirements.txt
│
└── frontend/                         # 前端 (Vue 3 + TypeScript)
    └── src/
        ├── App.vue                   # 根组件 + 路由 + 导航（登录/报价历史/改密）
        ├── main.ts                   # 路由注册 + 会话恢复 + 登录路由守卫
        ├── pages/
        │   ├── QuoterPage.vue        # 报价主页面（登录拦截 + 批量上传+卡片列表+合计）
        │   ├── QuotesHistoryPage.vue # 报价历史页面（分页+详情+删除）
        │   └── AdminPage.vue         # 管理后台页面
        ├── components/
        │   ├── login/
        │   │   ├── LoginModal.vue        # 全局登录/注册模态框
        │   │   └── AuthForm.vue          # 登录/注册表单（含验证码）
        │   ├── ChangePasswordDialog.vue  # 修改密码对话框
        │   ├── FileUpload.vue        # 文件拖拽上传
        │   ├── QuoteCard.vue         # 报价卡片（缩略图+参数+价格，自动报价）
        │   ├── FilePreviewCard.vue   # 文件预览卡片（缩略图+信息）
        │   ├── ModelPreview.vue      # Three.js 全功能3D预览
        │   ├── PreviewModal.vue      # 全屏预览弹窗
        │   ├── MaterialSelectModal.vue # 材料选择弹窗（分类+详情）
        │   ├── MaterialCard.vue      # 材料卡片（图片+名称+价格）
        │   ├── ParameterPanel.vue    # 参数面板（材料/表面处理/数量/交期，变更自动触发报价）
        │   ├── SurfaceTreatmentSection.vue # 表面处理多选
        │   ├── PaintSubOptionDialog.vue  # 喷漆子选项（哑光/高光+颜色）
        │   ├── PantoneColorPicker.vue # 潘通色板颜色选择器
        │   ├── DeliveryTimeSelector.vue # 交期选择器
        │   ├── PriceDisplay.vue      # 价格展示组件（纯展示）
        │   ├── InfoTooltip.vue       # 信息提示气泡
        │   ├── QuoteResult.vue       # 报价结果展示（含折扣/划线价）
        │   ├── StatusBadge.vue       # 报价状态徽章
        │   └── admin/                # 管理后台组件
        │       ├── AdminLogin.vue        # Token 认证登录
        │       ├── MaterialEditor.vue    # 材料管理
        │       ├── PostProcessEditor.vue # 后处理管理
        │       ├── DeliveryEditor.vue    # 交期选项管理
        │       ├── ProcessMappingEditor.vue # 工艺映射管理
        │       ├── MachineLimitsEditor.vue  # 设备体积限制管理
        │       └── SettingsEditor.vue    # 全局设置（费率/最低价/难度系数/支撑成本/折扣阶梯）
        ├── composables/
        │   ├── useQuoteApi.ts        # 报价 API + 报价历史 API（含 Auth Header）
        │   ├── useAuth.ts            # 用户认证状态管理（登录/注册/改密）
        │   └── useAdminApi.ts        # 管理后台 API 调用
        ├── data/
        │   ├── material-categories.ts # 材料分类定义
        │   └── pantone-colors.ts     # 潘通色板数据
        ├── types/api.ts              # TypeScript 类型定义
        └── utils/format.ts           # 格式化工具
```

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- [PrusaSlicer](https://www.prusa3d.com/page/prusaslicer_424/)（仅 FDM 切片需要）

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 复制环境变量（按需修改 PrusaSlicer 路径）
cp .env.example .env

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

首次启动会自动创建 SQLite 数据库并写入种子数据。日志中会打印 Admin Token。

### 前端启动

```bash
cd frontend

npm install
npm run dev
```

浏览器访问 `http://localhost:3000` 即可使用。

---

## 报价计算原理

系统采用 **策略模式（Strategy Pattern）** 设计，每种制造工艺有独立的报价策略类。所有报价策略都继承自 `PricingStrategy` 抽象基类，由 `PricingStrategyFactory` 根据用户选择的工艺自动路由。

### 1. FDM 3D 打印

> 文件位置：`backend/app/services/pricing/fdm_strategy.py`

FDM 是唯一会调用 PrusaSlicer 进行真实切片的工艺，报价数据最精确。

```
材料成本 = 切片耗材重量(g) × 材料单价(¥/g)
时间成本 = 切片打印时间(h) × 机器费率(¥/h)
支撑成本 = 支撑材料重量(g) × 材料单价(¥/g)    ← 几何估算
难度加价 = (材料成本 + 时间成本) × 难度系数    ← SA/V 比驱动
基础价格 = 材料成本 + 时间成本 + 支撑成本 + 难度加价 + 后处理费用 + 交期加急费
单价     = 基础价格 × 加价率(1.3) - 数量折扣
单价     = max(单价, 最低起订价)
总价     = 单价 × 数量
```

**示例**：PLA 材料、打印 2 小时、耗材 30g、SA/V 比中等(难度系数1.1)、标准交期
```
材料成本 = 30g × ¥0.18/g = ¥5.40
时间成本 = 2h × ¥35/h    = ¥70.00
支撑成本 = 30g×15% × ¥0.18/g = ¥0.81
难度加价 = (¥5.40 + ¥70.00) × 0.1 = ¥7.54
基础价格 = ¥5.40 + ¥70.00 + ¥0.81 + ¥7.54 = ¥83.75
单价     = ¥83.75 × 1.3   = ¥108.88
```

### 2. SLA 光固化

> 文件位置：`backend/app/services/pricing/sla_strategy.py`

SLA 按树脂体积计费，时间按层数 × 曝光时间估算。

```
模型体积(cm³) = 网格分析体积(mm³) ÷ 1000
材料成本 = 模型体积(cm³) × 树脂单价(¥/cm³)
打印时间 = 层数 × 每层曝光时间(8s) ÷ 3600
时间成本 = 打印时间(h) × 机器费率(¥/h)
难度加价 = (材料成本 + 时间成本) × 难度系数
基础价格 = 材料成本 + 时间成本 + 难度加价 + 后处理费用 + 交期加急费
单价     = 基础价格 × 加价率(1.3) - 数量折扣
单价     = max(单价, 最低起订价)
```

### 3. SLS / MJF 粉末烧结

SLS 和 MJF 复用 SLA 的报价策略，区别在于材料按重量（¥/g）计费而非体积。

```
材料重量(g) = 模型体积(cm³) × 材料密度(g/cm³)
材料成本 = 材料重量(g) × 材料单价(¥/g)
```

### 4. CNC 数控加工

> 文件位置：`backend/app/services/pricing/cnc_strategy.py`

CNC 按毛坯材料 + 加工工时计费，有最低起订金额。

```
毛坯体积 = 包围盒体积 × 1.1（10% 加工余量）
毛坯重量 = 毛坯体积(cm³) × 材料密度(g/cm³) ÷ 1000 (→ kg)
材料成本 = 毛坯重量(kg) × 材料单价(¥/kg)
加工工时 = max(体积×0.02 + 表面积×0.005 + 0.5, 0.5) 小时
加工费用 = 加工工时 × 机床费率(¥/h)
装夹费用 = ¥50（固定）
基础价格 = 材料成本 + 加工费用 + 装夹费用 + 后处理费用 + 交期加急费
单价     = max(基础价格 × 加价率 - 数量折扣, ¥50)  ← 最低起订 ¥50
总价     = 单价 × 数量
```

### 难度系数定价

> 文件位置：`backend/app/services/pricing/utils.py` → `calc_difficulty_surcharge`

系统通过 **表面积/体积比（SA/V ratio）** 自动识别打印难度较高的模型（薄壁件、精细件、复杂结构）。SA/V 比越高，意味着单位体积的表面积越大，打印越困难。

```
SA/V ratio = 模型表面积(mm²) / 模型体积(mm³)

难度评分 = clamp((SA/V - ratio_low) / (ratio_high - ratio_low), 0, 1)
3D打印难度系数 = 1.0 + coefficient × 难度评分     ← 最高 1.3
CNC难度系数   = 1.0 + cnc_coefficient × 难度评分   ← 最高 1.1

难度加价 = (材料成本 + 时间成本) × (难度系数 - 1.0)
```

默认配置：

| 参数 | 值 | 说明 |
|------|----|------|
| `ratio_low` | 0.3 /mm | 低于此值视为简单件，不加价 |
| `ratio_high` | 2.0 /mm | 高于此值视为最高难度 |
| `coefficient` | 0.30 | 3D 打印最大加价系数（最高加价 30%） |
| `cnc_coefficient` | 0.10 | CNC 最大加价系数（最高加价 10%） |

难度系数可在管理后台全局设置中编辑。

### 支撑成本

> 文件位置：`backend/app/services/pricing/utils.py` → `calc_support_cost`

FDM 打印的悬空部分需要支撑材料，系统基于模型几何特征估算支撑重量并独立计费。

```
支撑重量 = 模型重量(g) × support_percent%
支撑成本 = 支撑重量(g) × 材料单价(¥/g)
```

默认配置：

| 参数 | 值 | 说明 |
|------|----|------|
| `support_percent` | 15% | 支撑占模型重量百分比 |
| `support_price_per_gram` | ¥0 | 支撑材料单价，0 表示与主材同价 |

支撑成本可在管理后台全局设置中编辑。

### 后处理费用

> 文件位置：`backend/app/services/pricing/utils.py`

后处理费用有两种计算模式，可叠加：

| 模式 | 说明 | 示例 |
|------|------|------|
| `fixed` | 固定费用，直接加 | 攻丝 +¥5 |
| `percentage` | 百分比加价，基于（材料成本+时间成本） | 喷漆 +20% |

当前定价：

| 后处理 | 模式 | 价格 |
|--------|------|------|
| 打磨 | percentage | 15% |
| 喷漆 | percentage | 20% |
| 抛光 | percentage | 20% |
| 阳极氧化 | percentage | 25% |
| 电镀 | percentage | 30% |
| 支撑拆除 | percentage | 8% |
| 攻丝/攻牙 | fixed | ¥5 |
| 热处理 | fixed | ¥50 |
| UV后固化 | fixed | ¥8 |
| 渗透强化 | fixed | ¥20 |
| 染色 | fixed | ¥12 |

### 交期加急费用

交期加急费**仅对时间成本部分**加价，不对全价加价：

| 交期 | 加价系数 | 实际效果 |
|------|----------|----------|
| 标准 (3天) | ×1.0 | 无额外费用 |
| 加急 (2天) | ×1.15 | 时间成本 +15% |
| 特急 (1天) | ×1.35 | 时间成本 +35% |

```
交期加急费 = 时间成本 × (加价系数 - 1.0)
```

### 数量折扣

> 文件位置：`backend/app/services/pricing/utils.py` → `calc_quantity_discount`

批量订单自动享受阶梯折扣，可在管理后台编辑：

| 数量 | 折扣率 |
|------|--------|
| 1+件 | 0% |
| 5+件 | 3% |
| 10+件 | 6% |
| 20+件 | 9% |
| 50+件 | 12% |

```
折扣金额 = 单价 × 折扣率
实际单价 = 单价 - 折扣金额
```

### 最低起订价

> 文件位置：`backend/app/services/pricing/utils.py` → `apply_minimum_order`

各工艺设有最低起订金额，低于此金额的订单按最低价收取：

| 工艺 | 最低起订价 |
|------|-----------|
| FDM | ¥5 |
| SLA | ¥10 |
| SLS | ¥10 |
| MJF | ¥10 |
| CNC | ¥50 |

### 完整计算流程

```
用户上传模型 → 网格分析（体积/面积/水密性/面片数）
                    ↓
        FDM 工艺？──→ 是 → PrusaSlicer 切片 → 获取精确耗材重量和打印时间
                    ↓
                    否 → 基于几何数据估算
                    ↓
        策略工厂选择对应报价策略
                    ↓
        计算: 材料成本 + 时间成本
                    ↓
        叠加: 支撑成本（FDM 几何估算）
                    ↓
        叠加: 难度加价（SA/V 比驱动）
                    ↓
        叠加: 后处理费用（用户选择的后处理项）
                    ↓
        叠加: 交期加急费（仅对时间成本加价）
                    ↓
        基础价格 × 加价率 = 标记单价
                    ↓
        减去: 数量折扣（阶梯折扣率）
                    ↓
        取 max(折扣后单价, 最低起订价) = 最终单价
                    ↓
        最终单价 × 数量 = 总价
```

---

## 如何修改报价参数

系统支持三种方式修改报价参数，推荐使用管理后台：

### 1. 通过管理后台（推荐）

启动服务后，访问前端 `/admin` 路径进入管理后台。可在线修改：

- **材料管理**：单价、密度、分类、材料介绍、示例图片
- **后处理管理**：计费模式（固定/百分比）、价格、说明介绍
- **交期管理**：加价系数、天数
- **工艺映射**：各工艺可用的材料和后处理选项
- **设备限制**：各工艺的最大构建体积
- **全局设置**：
  - 基础费率（机器时间费率、加价率、CNC装夹费、CNC最低订单）
  - 各工艺最低起订价（FDM/SLA/SLS/MJF/CNC 独立设置）
  - 难度系数定价（SA/V 低阈值、高阈值、加价系数、CNC 系数）
  - 支撑成本配置（支撑重量百分比、支撑材料单价）
  - 数量折扣阶梯（最低数量、折扣率、显示标签，支持添加/删除阶梯）

修改后立即生效，无需重启服务。

### 2. 通过数据库直接修改

数据存储在 `backend/data/auto3dquote.db`（SQLite），可直接用 SQL 或数据库工具修改。

### 3. 通过 config.py 修改默认值

`backend/app/core/config.py` 中的值是种子数据的来源。修改这些值后，需要**删除数据库文件**并重启服务，新的种子数据才会写入。

```python
MATERIAL_PRICING: dict[str, dict] = {
    # 修改 price 值即可调整单价
    "PLA":   {"price": 0.18, "unit": "g",  "density": 1.24, "process": "fdm", "label": "PLA"},
    # ...
}

# 最低起订价
MINIMUM_ORDER_PER_PROCESS: dict[str, float] = {
    "fdm": 5.0, "sla": 10.0, "sls": 10.0, "mjf": 10.0, "cnc": 50.0,
}

# 难度系数定价
DIFFICULTY_PRICING: dict = {
    "ratio_low": 0.3,
    "ratio_high": 2.0,
    "coefficient": 0.30,
    "cnc_coefficient": 0.10,
    "enabled": True,
}

# 支撑成本配置
SUPPORT_PRICING: dict = {
    "enabled": True,
    "support_percent": 15.0,
    "support_price_per_gram": 0.0,
}

# 数量折扣阶梯
QUANTITY_DISCOUNT_TIERS: list[dict] = [
    {"min_qty": 1,  "discount": 0.00, "label": "1+件"},
    {"min_qty": 5,  "discount": 0.03, "label": "5+件 (-3%)"},
    {"min_qty": 10, "discount": 0.06, "label": "10+件 (-6%)"},
    {"min_qty": 20, "discount": 0.09, "label": "20+件 (-9%)"},
    {"min_qty": 50, "discount": 0.12, "label": "50+件 (-12%)"},
]
```

字段说明：
- `price`：单价（¥/g 或 ¥/cm³ 或 ¥/kg，取决于 `unit`）
- `unit`：计价单位（`g` = 克，`cm3` = 立方厘米，`kg` = 千克）
- `density`：材料密度（g/cm³），用于体积/重量换算
- `label`：前端显示的中文名称
- `category`：材料分类（`resin`/`nylon`/`metal`/`other`）
- `description`：材料介绍（支持多行描述）
- `machine_rate`：CNC 机床费率（仅 CNC 材料需要）

### 4. 通过 .env 文件覆盖

标量类型的配置可通过 `backend/.env` 文件覆盖，无需修改源代码：

```env
# .env 示例
TIME_COST_PER_HOUR=40.0
BASE_MARKUP_RATE=1.5
PRUSA_SLICER_PATH=D:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe
```

> 注意：字典类型的配置（如 `MATERIAL_PRICING`）不适合通过 .env 修改。

---

## 支持的材料与工艺

| 工艺 | 材料 | 计价方式 |
|------|------|----------|
| **FDM** | PLA (¥0.18/g), PETG (¥0.25/g), ABS (¥0.22/g), TPU (¥0.32/g), 尼龙 (¥0.45/g) | 重量(克) × 单价 |
| **SLA** | 标准树脂 (¥0.50/cm³), 韧性树脂 (¥0.80/cm³), 耐高温树脂 (¥1.00/cm³), 柔性树脂 (¥0.65/cm³) | 体积(cm³) × 单价 |
| **SLS** | PA12 (¥0.55/g), PA11 (¥0.65/g), PA12+玻珠 (¥0.70/g), TPU粉末 (¥0.85/g) | 重量(克) × 单价 |
| **MJF** | PA12 (¥0.55/g), PA11 (¥0.65/g) | 重量(克) × 单价 |
| **CNC** | 铝6061 (¥35/kg), 铝7075 (¥55/kg), 不锈钢304 (¥28/kg), 不锈钢316 (¥45/kg), 黄铜 (¥50/kg), 钛合金TC4 (¥280/kg) | 毛坯重量(kg) × 单价 + 加工费 |

---

## API 接口

### 获取报价 `POST /api/v1/quote`

> **需要登录**：请求需携带 `Authorization: Bearer <token>` 头，未认证返回 422。

**参数**（`multipart/form-data`）：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `file` | File | 必填 | 3D 模型文件（.stl/.obj/.3mf/.stp/.step） |
| `process` | string | `"fdm"` | 工艺类型：fdm/sla/sls/mjf/cnc |
| `material` | string | `"PLA"` | 材料类型 |
| `quality` | string | `"standard"` | 质量：draft/standard/high |
| `quantity` | int | `1` | 数量 (1-1000) |
| `post_processing` | string | `""` | 后处理选项，逗号分隔 |
| `delivery` | string | `"standard"` | 交期：standard/express/urgent |
| `paint_options` | string | `""` | 喷漆子选项 JSON，如 `{"finish":"matte","color":"#FF0000"}` |

**响应字段**（`CostBreakdown`）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `material_cost` | MaterialCost | 材料成本明细 |
| `time_cost` | TimeCost | 时间成本明细 |
| `post_process_costs` | PostProcessCost[] | 后处理费用列表 |
| `delivery_surcharge` | float | 交期加急费 |
| `difficulty_score` | float | 难度评分 (0.0~1.0) |
| `difficulty_multiplier` | float | 难度系数 (1.0=无加价) |
| `difficulty_surcharge` | float | 难度加价金额 (¥) |
| `support_weight` | float | 支撑材料重量 (g) |
| `support_cost` | float | 支撑材料成本 (¥) |
| `quantity_discount` | float | 数量折扣金额 (¥) |
| `quantity_discount_rate` | float | 数量折扣率 (如 0.06 = 6%) |
| `base_price` | float | 基础价格（成本合计） |
| `markup_rate` | float | 实际加价率 |
| `unit_price` | float | 最终单价 |
| `quantity` | int | 数量 |
| `total_price` | float | 总价 |

### 获取选项列表 `GET /api/v1/materials`

返回完整的工艺-材料-后处理-交期选项树，前端参数面板基于此渲染。材料包含 `category`、`image_url`、`description` 字段；后处理包含 `description` 字段；交期包含 `days` 字段。

### STEP 文件转换 `POST /api/v1/convert`

将 STEP/STP 文件转换为 STL 格式，用于前端预览。

**参数**：`multipart/form-data`，字段 `file`。

### 健康检查 `GET /api/v1/health`

检查服务状态和 PrusaSlicer 可用性。

---

## 用户系统

系统内置用户认证功能，注册/登录后才能使用报价服务。

### 认证流程

1. 用户通过注册接口创建账号（需验证码）
2. 登录后获取 JWT Token（有效期 7 天）
3. 前端将 Token 存储在 localStorage，每次请求携带 `Authorization: Bearer <token>`
4. 报价请求自动保存为历史记录

### 用户认证接口

所有路径前缀为 `/api/v1/auth`。

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/auth/captcha` | 获取图片验证码 | 否 |
| POST | `/auth/register` | 注册新用户（需验证码），返回 JWT | 否 |
| POST | `/auth/login` | 用户名+密码登录，返回 JWT | 否 |
| GET | `/auth/me` | 获取当前用户信息 | 是 |
| PUT | `/auth/password` | 修改密码（验证旧密码） | 是 |

### 报价历史接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/auth/quotes` | 获取报价记录列表（分页），管理员可查看所有用户 | 是 |
| GET | `/auth/quotes/{id}` | 获取报价记录详情（含完整成本明细） | 是（校验归属） |
| DELETE | `/auth/quotes/{id}` | 删除报价记录 | 是（校验归属） |

### 用户角色

| 角色 | 权限 |
|------|------|
| `user` | 报价、查看自己的历史记录、修改密码 |
| `admin` | 所有 user 权限 + 管理后台访问 + 查看所有用户报价记录 |

### 管理员账号

在 `backend/.env` 中配置管理员种子账号：

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_password
```

首次启动时自动创建，已存在则跳过。

---

## 管理后台

管理后台提供在线配置管理功能，访问前端 `/admin` 路径即可使用。

### 认证

启动后端时会在日志中打印 Admin Token（如果未在 .env 中配置 `ADMIN_TOKEN`），用于 API 认证。

### 管理界面

| 标签页 | 功能 |
|--------|------|
| 材料 | 新增/编辑/删除材料，上传图片，设置单价/密度/分类/介绍 |
| 后处理 | 新增/编辑/删除后处理，设置计费模式(固定/百分比)和价格 |
| 交期 | 编辑各档位加价系数和天数 |
| 映射 | 管理各工艺可用的材料和后处理选项 |
| 设备 | 设置各工艺最大构建体积 (X/Y/Z mm) |
| 设置 | 结构化编辑基础费率、最低起订价、难度系数、支撑成本、数量折扣阶梯 |

### 管理接口

所有管理接口路径前缀为 `/api/v1/admin`，需要 Bearer Token 认证。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/config` | 获取完整配置快照 |
| GET | `/admin/materials` | 获取所有材料列表 |
| POST | `/admin/materials` | 新增材料 |
| PUT | `/admin/materials/{id}` | 更新材料 |
| DELETE | `/admin/materials/{id}` | 删除材料 |
| POST | `/admin/materials/{id}/image` | 上传材料图片 |
| GET | `/admin/post-processes` | 获取所有后处理列表 |
| POST | `/admin/post-processes` | 新增后处理 |
| PUT | `/admin/post-processes/{id}` | 更新后处理 |
| DELETE | `/admin/post-processes/{id}` | 删除后处理 |
| GET | `/admin/delivery-options` | 获取交期选项 |
| PUT | `/admin/delivery-options/{id}` | 更新交期选项 |
| GET | `/admin/process-mapping` | 获取工艺映射 |
| PUT | `/admin/process-mapping/{id}/materials` | 更新工艺-材料映射 |
| PUT | `/admin/process-mapping/{id}/post-processes` | 更新工艺-后处理映射 |
| GET | `/admin/machine-limits` | 获取设备体积限制 |
| PUT | `/admin/machine-limits/{id}` | 更新设备体积限制 |
| GET | `/admin/settings` | 获取全局设置 |
| PUT | `/admin/settings/{key}` | 更新全局设置 |
| POST | `/admin/cache/refresh` | 刷新配置缓存 |

---

## 数据库说明

系统使用 SQLite 数据库，文件位于 `backend/data/auto3dquote.db`。

### 核心表

| 表名 | 说明 |
|------|------|
| `users` | 用户账号（用户名、密码哈希、角色、状态） |
| `quote_records` | 报价历史记录（关联用户、文件名、工艺、材料、价格明细、模型数据） |
| `materials` | 材料信息（单价、密度、分类、图片、介绍等） |
| `post_processes` | 后处理选项（计费模式、价格、说明） |
| `delivery_options` | 交期选项（加价系数、天数） |
| `machine_volume_limits` | 各工艺设备构建体积限制 |
| `global_settings` | 全局配置（时间费率、加价率、最低起订价、难度系数、支撑成本、折扣阶梯等） |
| `process_materials` | 工艺-材料关联（含排序） |
| `process_post_processes` | 工艺-后处理关联（含排序） |

### 配置缓存机制

`ConfigService` 在首次请求时从数据库加载所有配置到内存缓存，后续 API 直接使用缓存数据。通过管理后台修改配置后会自动刷新缓存，也可手动调用 `/admin/cache/refresh` 接口刷新。

---

## 后续计划

- [x] 用户系统与报价历史
- [x] 登录后才能报价
- [x] 报价历史记录查看/删除
- [x] 修改密码功能
- [ ] 购物车与在线支付
- [ ] 对接真实生产排期系统
- [ ] 支持 IGES 格式
- [ ] 本地 PrusaSlicer 切片优化（确保与云端一致的结果）

---

## 开源协议

MIT License
