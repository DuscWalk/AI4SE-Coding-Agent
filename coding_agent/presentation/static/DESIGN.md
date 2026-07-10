# DESIGN.md · Coding Agent Harness

> **Open Design 设计系统**：选用 `linear-app`（来源：[nexu-io/open-design](https://github.com/nexu-io/open-design) 仓库 `design-systems/linear-app/`）。
> **Skill**：`prototype` — 生成单页 Web 应用界面。
> **设计令牌来源**：`tokens.css`（本目录），与 Open Design 的 `design-systems/linear-app/tokens.css` 保持一致。

## 设计系统选择理由

Linear 是开发者工具领域最受推崇的设计系统之一。其 dark-mode-first、极简、精确的风格天然适合 Coding Agent Harness 这一面向开发者的控制台工具：

- **Dark-mode-native**：近黑画布（`#08090a`）+ 半透明白色边框，信息密度通过亮度层级管理
- **单色系 + 单一强调色**：除了 indigo-violet（`#5e6ad2`）用于 CTA 和交互态外，其余全部灰阶
- **Inter Variable 字体**：配合 `cv01`/`ss03` OpenType 特性，510 字重为核心 UI 字重
- **亮度阶梯替代阴影**：在暗色表面上不使用传统阴影，而是通过背景亮度步进（`0.02 → 0.04 → 0.05`）来表现层级

## 完整设计规范

详见 Open Design 仓库中的原始文件：
- **设计系统**：`design-systems/linear-app/DESIGN.md`（9 节完整规范）
- **令牌**：`design-systems/linear-app/tokens.css`（56 个 CSS 自定义属性）
- **组件清单**：`design-systems/linear-app/components.manifest.json`（9 个组件组）

## 本项目使用的组件

| 组件 | 对应 Linear 模式 | 用途 |
|------|-----------------|------|
| App Shell | 侧边栏 + 主内容区 | 全局布局 |
| Ghost Button | `.btn-ghost` | 次要操作（取消、清除） |
| Primary Button | `.btn-primary` | 主要 CTA（提交任务） |
| Card | `.card` | 面板容器 |
| Pill | `.pill` | 状态标签（RUNNING/COMPLETED/FAILED） |
| Field | `.field` | 输入框 + 标签 |
| Terminal | 自定义（类 Warp 风格） | 步骤日志 |
| Command Bar | 自定义（类 Linear 搜索框） | 任务输入