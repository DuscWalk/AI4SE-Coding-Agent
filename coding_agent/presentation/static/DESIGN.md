# DESIGN.md · Coding Agent Harness

> 遵循 Open Design 规范的设计系统文件。本文档是前端 UI 的单一品牌真相来源，编码智能体可据此生成一致的前端界面。

## 1. Color

### 1.1 基础色板（Tokyo Night Dark）

| Token | Hex | HSL | 用途 |
|-------|-----|-----|------|
| `--color-bg` | #1a1b26 | 234 18% 13% | 页面背景 |
| `--color-surface` | #24283b | 233 21% 19% | 面板/卡片背景 |
| `--color-surface-hover` | #36416a | 228 26% 31% | 悬停态 |
| `--color-border` | #3b4261 | 228 23% 31% | 边框/分割线 |
| `--color-border-focus` | #7aa2f7 | 220 89% 72% | 聚焦态边框 |

### 1.2 语义色

| Token | Hex | 用途 |
|-------|-----|------|
| `--color-text-primary` | #c0caf5 | 主文本 |
| `--color-text-secondary` | #565f89 | 辅助文本/占位符 |
| `--color-accent` | #7aa2f7 | 主色调/链接/按钮 |
| `--color-danger` | #f7768e | 错误/危险操作 |
| `--color-success` | #9ece6a | 成功状态 |
| `--color-warning` | #e0af68 | 警告/审批 |

### 1.3 语义色变体（半透明叠加）

| Token | 用途 |
|-------|------|
| `--color-danger-bg` | 错误背景（danger @ 10% opacity） |
| `--color-success-bg` | 成功背景（success @ 10% opacity） |
| `--color-warning-bg` | 警告背景（warning @ 10% opacity） |

## 2. Typography

### 2.1 字体族

| Token | 值 | 用途 |
|-------|-----|------|
| `--font-sans` | `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | 正文/UI |
| `--font-mono` | `"Cascadia Code", "Fira Code", "JetBrains Mono", Consolas, monospace` | 代码/日志 |

### 2.2 字号阶梯

| Token | 值 | 用途 |
|-------|-----|------|
| `--text-xs` | 11px | 元数据/时间戳 |
| `--text-sm` | 13px | 辅助文本/状态标签 |
| `--text-base` | 14px | 正文 |
| `--text-lg` | 16px | 面板标题 |
| `--text-xl` | 20px | 页面标题 |

### 2.3 字重

| Token | 值 |
|-------|-----|
| `--font-normal` | 400 |
| `--font-medium` | 500 |
| `--font-semibold` | 600 |

## 3. Spacing

基于 4px 基准的间距系统：

| Token | 值 | 用途 |
|-------|-----|------|
| `--space-1` | 4px | 内边距/紧凑间距 |
| `--space-2` | 8px | 按钮间距/元素间距 |
| `--space-3` | 12px | 卡片内边距 |
| `--space-4` | 16px | 面板间距/区块间距 |
| `--space-5` | 20px | 面板内边距 |
| `--space-6` | 24px | 页面边距/区块间距 |

## 4. Layout

### 4.1 网格

- 主布局：2 列网格（`grid-template-columns: 1fr 1fr`），间距 `--space-4`
- 响应式断点：`max-width: 900px` → 单列布局
- 最大内容宽度：1400px，居中

### 4.2 圆角

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius-sm` | 4px | 按钮/输入框/标签 |
| `--radius-md` | 8px | 面板/卡片 |
| `--radius-full` | 12px | 状态指示器 |

## 5. Components

### 5.1 按钮

- 主按钮：`background: var(--color-accent)`, `color: var(--color-bg)`, `border-radius: --radius-sm`
- 危险按钮：`background: var(--color-danger)`
- 成功按钮：`background: var(--color-success)`
- 次要按钮：`background: var(--color-border)`, `color: var(--color-text-primary)`
- 禁用态：`opacity: 0.4`, `cursor: not-allowed`
- 悬停态：`opacity: 0.9`（主按钮）/ `opacity: 0.7`（文字按钮）

### 5.2 输入框

- 背景：`var(--color-bg)`，边框：`var(--color-border)`，圆角：`--radius-sm`
- 聚焦态：`border-color: var(--color-accent)`
- 占位符：`color: var(--color-text-secondary)`

### 5.3 面板（Panel）

- 背景：`var(--color-surface)`，边框：`1px solid var(--color-border)`，圆角：`--radius-md`
- 标题：`color: var(--color-accent)`, `font-size: --text-lg`, `font-weight: --font-semibold`

### 5.4 步骤卡片（Step Card）

- 左侧 3px 色带指示状态：绿色=成功，红色=错误，黄色=警告，蓝色=信息
- 悬停：`background: var(--color-surface-hover)`

### 5.5 状态标签

- 圆角：`--radius-full`，字号：`--text-xs`
- RUNNING：黄色背景 + 脉冲动画
- COMPLETED：绿色背景
- FAILED：红色背景
- CANCELLED：灰色背景

## 6. Motion

| Token | 值 | 用途 |
|-------|-----|------|
| `--transition-fast` | 0.2s ease | 悬停/聚焦过渡 |
| `--transition-normal` | 0.2s ease | 背景过渡 |
| `--animation-pulse` | 2s ease-in-out infinite | 运行状态脉冲 |

- 原则：动画仅用于状态指示（脉冲），交互反馈使用即时过渡。避免装饰性动画。
- 禁用态使用 `opacity` 过渡而非颜色变化。

## 7. Voice

- **调性**：专业、简洁、技术感。这是一个开发者工具，不是消费品。
- **术语**：使用技术术语（session、step、approval、credential），不翻译为"会话""步骤"等。
- **错误信息**：直接说明问题，不添加"抱歉""请"等社交用语。例："Network error: timeout"而非"抱歉，网络似乎出现了问题"。
- **状态标签**：使用英文（RUNNING/COMPLETED/FAILED/CANCELLED），符合开发者习惯。

## 8. Brand

- **产品名**：Coding Agent Harness
- **标识**：纯文字标识，无图标。标题使用 `--color-accent` 色。
- **定位**：面向开发者的编码智能体控制台，强调可控性和可观测性。

## 9. Anti-Patterns

- **禁止**：使用 emoji 作为 UI 元素（状态指示器除外）
- **禁止**：渐变背景或阴影效果——保持扁平、硬朗的技术工具风格
- **禁止**：超过 2 列的复杂布局——此工具的核心操作流是线性的（输入→监控→审批→历史）
- **禁止**：自定义滚动条样式在不支持 `::-webkit-scrollbar` 的浏览器中无降级方案
- **禁止**：在 900px 以下宽度保持双列布局