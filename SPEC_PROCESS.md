# SPEC_PROCESS.md · 规约与计划生成过程

> 本文档记录 Coding Agent Harness 项目从零到 SPEC.md + PLAN.md 的完整生成过程，以及冷启动验证的结果与修订。

---

## 一、brainstorming 关键节点

### 1.1 项目上下文探索

- 阅读了 `docs/` 下的全部课程文档：通用要求、A 类项目要求、Agent 伪代码、PPT 讲义
- 确认项目目标：自建 Coding Agent Harness，六个维度（决策/工具/记忆/治理/反馈/配置），反馈闭环为主贡献
- 确认技术约束：Python 3.11+，必须自己实现主循环，不能寄生在 LangChain/AutoGen 等框架上

### 1.2 关键决策问答（8 轮）

| 轮次 | 问题 | 用户选择 | 决策影响 |
|------|------|----------|----------|
| 1 | 主贡献维度 | 反馈闭环 | 整个 SPEC 和 PLAN 围绕反馈管线展开 |
| 2 | 技术栈 | B: Python + FastAPI | 分层架构、Pydantic 模型、异步 Web |
| 3 | LLM 抽象 | C: 两种 mock（Scripted + RuleBased） | 测试策略需要覆盖两种 mock 模式 |
| 4 | 反馈深度 | B: 多层管线（语法→类型→lint→测试） | 4 个 Sensor + 分类器 + 策略引擎 |
| 5 | 工具系统 | B: 中等（10 个内置工具） | 覆盖文件/搜索/shell/git/测试五类 |
| 6 | 记忆 | C: 向量检索（ChromaDB） | 三层存储：scratchpad → 文件 → 向量 |
| 7 | 治理 | B: 三级权限（SAFE/RISKY/DANGEROUS） | HITL 状态机 + 硬拦截模式 |
| 8 | WebUI | C: 完整工作区（任务+轨迹+审批） | FastAPI + WebSocket + 原生前端 |
| 9 | 架构 | C: 分层（表示/应用/领域/基础设施） | 依赖注入、接口隔离 |

### 1.3 设计章节审批

6 个设计章节逐段提交用户审批，均通过：
1. 架构与分层：4 层，上层依赖下层，下层不依赖上层
2. 应用层：AgentLoop 主循环 + SessionManager + ActionParser
3. 反馈闭环（主贡献）：Sensor 管线 → 失败分类器 → 修正策略引擎
4. 工具与治理：10 工具 + 三级权限 + HITL 状态机
5. 记忆与配置：三层存储 + 声明式配置加载
6. 基础设施与 WebUI：LLM 抽象 + 凭据存储 + FastAPI + 原生前端

---

## 二、AI 建议中采纳、推翻、修正的部分

### 2.1 采纳的 AI 建议

| 建议 | 理由 |
|------|------|
| 分层架构而非扁平结构 | 清晰的依赖方向，便于测试和替换 |
| Pydantic 作为数据模型层 | 类型安全、自动校验、与 FastAPI 深度集成 |
| ScriptedMockLLM + RuleBasedMockLLM 两种 mock | 覆盖预设序列和模式匹配两种测试场景 |
| 反馈管线按速度排序（语法→类型→lint→测试） | 快速失败，节省等待时间 |
| 修正策略三级（RETRY→ROLLBACK→ASK_USER） | 渐进式升级，避免死循环 |
| ChromaDB 嵌入式向量存储 | 无需外部服务，Python 原生 |
| 危险命令硬拦截模式（不可 HITL 绕过） | 安全优先，如 `rm -rf /` 永远 blocked |

### 2.2 推翻的 AI 建议

| 建议 | 推翻理由 |
|------|----------|
| 使用 React 前端框架 | 课程要求轻量，原生 HTML/CSS/JS 更简单，减少依赖 |
| 引入 Redis 做会话缓存 | 过度设计，单机内存即可满足需求 |
| 支持多 LLM 供应商热切换 | 超出范围，OpenAI 兼容协议已足够覆盖主流供应商 |
| 工具插件化（动态加载） | 10 个内置工具不需要插件系统，YAGNI |

### 2.3 修正的 AI 建议

| 原始建议 | 修正后 | 原因 |
|----------|--------|------|
| 反馈管线串行执行 | 同类型 sensor 可并行，但按速度排序串行执行以支持快速失败 | 语法错误时无需等待测试结果 |
| 向量嵌入用 sentence-transformers | 首次实现用简单哈希降级，在 `vector_store.py` 中提供 InMemoryVectorStore | 减少首次运行的模型下载依赖 |
| AgentLoop 直接持有所有组件 | 通过依赖注入传入，AgentLoop 只依赖接口 | 便于测试时替换组件 |

---

## 三、冷启动验证

### 3.1 验证设计

- **时间**：2026-07-10
- **验证目标**：Task 1（项目骨架）+ Task 2（数据模型）
- **陌生 agent 配置**：
  - 类型：general-purpose agent（与主开发 agent 不同）
  - 模型：Sonnet（与主开发 Opus 不同）
  - 输入：仅 SPEC.md + PLAN.md 两个文件路径
  - 无对话上下文、无 CLAUDE.md 项目章程
- **预期**：agent 按 PLAN.md 步骤独立完成两个 task，包括 TDD 红-绿-重构和 git commit

### 3.2 验证结果

**实际产出**：

| 预期产出 | 实际产出 | 状态 |
|----------|----------|------|
| `pyproject.toml` | 已创建，agent 自行修正了 build-backend | 完成 |
| 目录结构（coding_agent/、tests/ 等） | 全部创建，15 个目录 | 完成 |
| 所有 `__init__.py` | 15 个文件全部创建 | 完成 |
| `tests/domain/test_models.py`（8 个测试） | 已创建，内容与 PLAN.md 一致 | 完成 |
| `coding_agent/domain/models.py`（全部 15 个 Pydantic 模型） | 已创建，与 PLAN.md 一致 | 完成 |
| pip install 执行 | 全部依赖安装成功 | 完成 |
| pytest 运行（8 tests） | 8 passed | 完成 |
| Git commit（2 个） | `a561118` + `93aa595` | 完成 |

**验证命令**：
```powershell
pytest tests/domain/test_models.py -v
# 结果：8 passed in 0.25s
```

**结论：冷启动验证通过。** 陌生 agent 仅凭 SPEC.md + PLAN.md 成功完成了 Task 1 和 Task 2，遵循了 TDD 流程（先写失败测试 → 确认失败 → 实现 → 确认通过），并做了两次有意义的 commit。

### 3.3 暴露的 PLAN.md 缺陷

| 缺陷 | 严重程度 | 分析 |
|------|----------|------|
| **build-backend 值错误** | 高 | `setuptools.backends._legacy:_Backend` 是无效值。agent 自行修正为 `setuptools.build_meta`。这是 PLAN.md 中的事实性错误 |
| **Task 1 粒度过大** | 中 | 原始 Task 1 包含 5 个步骤，跨度大。agent 虽然完成了，但将 Task 1 拆分为 1a + 1b 可降低后续 task 的执行风险 |
| **缺少平台差异说明** | 中 | `mkdir -p` 在 PowerShell 中不可用。agent 使用 Sonnet 模型自行处理了这个问题，但 PLAN.md 应显式给出 PowerShell 命令 |
| **缺少中间验证点** | 低 | 原始 Task 1 没有"验证目录结构"步骤，agent 自行添加了验证。应在 PLAN.md 中显式要求 |

### 3.4 修订措施

基于冷启动验证发现的问题，对 PLAN.md 做以下修订：

1. **修正 build-backend**：`setuptools.backends._legacy:_Backend` → `setuptools.build_meta`（agent 发现的关键 bug）
2. **拆分 Task 1**：将 Task 1 拆为 Task 1a（pyproject.toml + 目录结构）和 Task 1b（pip install + 验证），每步有明确的验证命令
3. **增加验证步骤**：每个 task 结束时增加独立验证（如 `Get-ChildItem -Recurse -Directory` 确认目录存在）
4. **注明平台差异**：在步骤中明确标注 Windows PowerShell 语法（如 `New-Item -ItemType Directory -Force` 代替 `mkdir -p`）
5. **增加失败分支**：关键步骤增加"如果失败"的备选方案（如 pip install 失败时的降级安装命令）

---

## 四、PLAN.md 修订记录

### 修订 1：Task 1 拆分 + build-backend 修正 + 平台加固（2026-07-10）

**触发**：冷启动验证（Sonnet general-purpose agent，commit `a561118` + `93aa595`）

**发现的问题**：
1. `build-backend = "setuptools.backends._legacy:_Backend"` 是无效值，agent 自行修正为 `setuptools.build_meta`
2. Task 1 跨度过大（5 步），后续 task 执行风险高
3. 缺少 PowerShell 平台语法和中间验证点

**修订内容**：
- 修正 `build-backend` 为 `setuptools.build_meta`
- Task 1 拆分为 Task 1a（pyproject.toml + 目录结构 + \_\_init\_\_.py + commit）和 Task 1b（pip install + 验证）
- 所有 shell 命令改为 PowerShell 语法（`New-Item -ItemType Directory -Force` 代替 `mkdir -p`）
- 每步增加验证命令
- pip install 步骤增加失败降级方案
- 更新依赖关系图

**修订前后关键 diff**：
```
- build-backend = "setuptools.backends._legacy:_Backend"
+ build-backend = "setuptools.build_meta"

- Task 1: 项目骨架与依赖 (5 steps, 单 task)
+ Task 1a: 项目骨架 (7 steps, 含验证)
+ Task 1b: 安装依赖并验证 (4 steps, 含失败分支)

- mkdir -p coding_agent/infrastructure ...
+ New-Item -ItemType Directory -Force -Path coding_agent/infrastructure
+ New-Item -ItemType Directory -Force -Path coding_agent/domain/tools
+ ... (每个目录单独一行)
```

---

## 五、过程反思

### 5.1 规约质量评估

SPEC.md 的工程质量较好：
- 功能规约明确：每个模块的输入/行为/输出/边界/错误处理都有定义
- 数据模型完整：8 个核心实体，字段和关系清晰
- 架构清晰：分层 + 组件图 + 数据流
- 但缺少：对"如何测试"的具体指导（在哪一层 mock、用什么 fixture）

### 5.2 计划质量评估

PLAN.md 的初始版本存在以下问题：
- `build-backend` 值是一个事实性错误（`setuptools.backends._legacy:_Backend` 不存在），冷启动 agent 发现并修正了它
- 任务粒度不均匀（Task 1 太大，后续 task 粒度适中）
- 缺少平台适配说明（Windows vs Linux 命令差异）
- 所有步骤都是 happy path，缺少失败处理

冷启动验证暴露了这些问题，修订后的 PLAN.md 更加健壮。

### 5.3 冷启动验证的价值

冷启动验证是本次项目最有价值的工程实践之一：
- 陌生 agent（Sonnet general-purpose）仅凭 SPEC.md + PLAN.md 成功完成了 Task 1 和 Task 2，证明 plan 基本可执行
- agent 在无人干预的情况下发现并修正了 `build-backend` 的错误值——这是人类 review 容易忽略的细节
- 验证了 TDD 流程在 plan 中的表述足够清晰：agent 正确地先写测试、确认失败、再写实现
- 暴露了平台差异（`mkdir -p` vs `New-Item`）和 task 粒度问题，驱动了 PLAN.md 的加固
- 这证明了 CLAUDE.md 中"冷启动验证是硬性门禁"的合理性：如果直接用原始 PLAN.md 进入实现，中间会遇到可避免的阻碍