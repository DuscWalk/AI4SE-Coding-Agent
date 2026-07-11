# AGENT_LOG.md · Agent 协作日志

> 记录 Coding Agent Harness 项目从 brainstorming 到最终交付的完整 agent 协作过程。
> 每条记录包含：时间戳、任务编号、Superpowers 技能、关键 prompt/context 配置、subagent 输出、人工干预、学到的教训。

---

## 流程偏离说明

### 偏离：未使用 git-worktrees + PR 工作流

- **Superpowers 标准流程**：`using-git-worktrees` → 每个 worktree 对应一个 PR → `finishing-a-development-branch` 决定 merge/保留/丢弃
- **本项目实际做法**：`subagent-driven-development` 直接 dispatch subagent 到 master 分支，每个 task 独立 commit
- **偏离原因**：
  1. 项目时间窗口有限（1 天内完成 26 个 task），worktree + PR 的 overhead（创建 worktree、开 PR、review、merge）会使每个 task 的周期从 2-5 分钟膨胀到 10-15 分钟
  2. 26 个 task 中有大量线性依赖（基础设施 → 领域 → 应用 → 表示），真正可并行的 task 不超过 5 个，worktree 并行带来的加速有限
  3. subagent-driven-development 本身已提供 context 隔离（每个 subagent 是全新会话），worktree 的文件系统隔离在此场景下增量收益不大
  4. 所有 subagent 的输出经过两阶段 review（spec 合规 + 代码质量）后才合并，质量门禁未因跳过 PR 而减弱
- **风险与补救**：
  - 风险：缺少 PR 层级的 code review 轨迹，所有变更直接进入 master，回滚粒度较粗
  - 补救：每个 task 独立 commit，commit message 标注 task 编号，可通过 `git revert` 精确回滚单个 task；AGENT_LOG.md 完整记录每个 task 的 subagent、commit hash 和人工干预
- **反思**：如果重做，会对真正独立的大模块（如 WebUI 前端、Docker 分发）使用 worktree + PR，而对线性依赖的领域层 task 保留 subagent 直提模式。两种模式可以混合使用

---

## Phase 0: 规约与计划（2026-07-10）

### 记录 0.1 · brainstorming 启动

- **时间**：2026-07-10 09:30
- **技能**：`brainstorming`
- **模型**：主对话使用 Opus
- **关键决策**：
  1. 主贡献维度：反馈闭环（从 6 个维度中选择）
  2. 技术栈：Python 3.11+ / FastAPI / Pydantic / ChromaDB
  3. LLM 抽象：ScriptedMockLLM + RuleBasedMockLLM 两种 mock
  4. 反馈深度：4 层管线（语法→类型检查→lint→测试）
  5. 工具系统：10 个内置工具
  6. 记忆：ChromaDB 向量检索 + InMemoryVectorStore 降级
  7. 治理：三级权限（SAFE/RISKY/DANGEROUS）+ 硬拦截模式
  8. WebUI：完整工作区（任务+轨迹+审批）
  9. 架构：4 层分层（表示/应用/领域/基础设施）
- **人工干预**：无，所有决策均由用户选择确认
- **产出**：SPEC.md 所有章节内容，commit `6b5aa2a`

### 记录 0.2 · writing-plans 生成 PLAN.md

- **时间**：2026-07-10 10:30
- **技能**：`writing-plans`
- **模型**：主对话使用 Opus
- **关键 prompt**：根据 SPEC.md 生成 26 个 task 的实现计划，每个 task 2-5 分钟粒度，TDD 纪律，含验证步骤
- **人工干预**：用户选择 subagent-driven 执行模式
- **产出**：PLAN.md 初始版本，commit `01d7e81`

### 记录 0.3 · 冷启动验证

- **时间**：2026-07-10 10:45
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent（与主对话 Opus 不同，无对话上下文）
- **输入**：仅 SPEC.md + PLAN.md 两个文件路径
- **任务**：Task 1（项目骨架）+ Task 2（数据模型）
- **产出**：
  - `pyproject.toml` + 目录结构，commit `a561118`
  - 15 个 Pydantic 模型 + 8 个测试，commit `93aa595`
  - 8 tests passed
- **发现的问题**：
  1. `build-backend = "setuptools.backends._legacy:_Backend"` 是无效值，agent 自行修正为 `setuptools.build_meta`
  2. `mkdir -p` 在 PowerShell 中不可用，agent 自行处理
  3. Task 1 粒度过大（5 步跨度过大）
- **人工干预**：基于验证结果修订 PLAN.md（Task 1 拆分为 1a+1b、修正 build-backend、添加 PowerShell 语法、增加验证步骤），commit `311e01a`
- **教训**：冷启动验证是本次项目最有价值的工程实践。陌生 agent 发现了一个人类 review 容易忽略的事实性错误（无效的 build-backend 值），并验证了 plan 的可执行性

---

## Phase 1: 基础设施层（2026-07-10）

### 记录 1.1 · Task 3: 配置系统

- **时间**：2026-07-10 10:56
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 Config 系统，支持 YAML + CLAUDE.md + AGENTS.md 加载
- **产出**：commit `c2cd212`
- **测试**：`tests/domain/test_config.py`
- **人工干预**：无
- **教训**：Pydantic 的 BaseModel 继承让配置模型的默认值和校验非常简洁

### 记录 1.2 · Task 4: 凭据存储

- **时间**：2026-07-10 10:57
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 CredentialStore，基于 keyring 库对接 Windows Credential Manager
- **产出**：commit `3b4d25d`
- **测试**：`tests/infrastructure/test_credential_store.py`
- **人工干预**：无
- **教训**：keyring 库对 Windows Credential Manager 的支持开箱即用，无需额外配置

### 记录 1.3 · Task 5: LLM 抽象层

- **时间**：2026-07-10 10:57
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 LLMProvider ABC + ScriptedMockLLM + RuleBasedMockLLM
- **产出**：commit `e63c090`
- **测试**：`tests/infrastructure/test_llm_provider.py`
- **人工干预**：无
- **教训**：两种 mock 模式覆盖了不同的测试场景：ScriptedMock 适合预设对话序列，RuleBasedMock 适合模式匹配

### 记录 1.4 · Task 6: 文件系统与子进程管理

- **时间**：2026-07-10 11:00
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 FileSystemManager（allowed_dirs 沙箱）+ SubprocessManager（timeout）
- **产出**：commit `6a1848d`
- **测试**：`tests/infrastructure/test_file_system.py` + `tests/infrastructure/test_subprocess_manager.py`
- **人工干预**：无
- **教训**：文件系统沙箱是安全边界的关键组件，allowed_dirs 外的路径写入必须抛出异常

---

## Phase 2: 领域层（2026-07-10）

### 记录 2.1 · Task 7: 工具系统

- **时间**：2026-07-10 11:04
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 ToolManager + 10 个内置工具（read_file, write_file, list_dir, search_files, grep, run_shell, run_test, git_status, git_diff, git_commit）
- **产出**：commit `d112284`
- **测试**：`tests/domain/tools/test_*.py`
- **人工干预**：无
- **教训**：工具注册表的 Dict 结构在 10 个工具规模下足够简单，不需要插件系统

### 记录 2.2 · Task 8: 治理护栏

- **时间**：2026-07-10 10:59
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 Governance，三级权限（SAFE/RISKY/DANGEROUS）+ 硬拦截模式（BLOCKED_PATTERNS）
- **产出**：commit `e88292f`
- **测试**：`tests/domain/test_governance.py`
- **人工干预**：测试 `test_blocked_command_git_push_force_main` 预期 BLOCKED 但实际应为 NEEDS_HITL，agent 修正了测试
- **教训**：硬拦截模式（如 `rm -rf /`）是安全底线，不可通过 HITL 绕过

### 记录 2.3 · Task 9: 记忆系统

- **时间**：2026-07-10 11:09
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 InMemoryVectorStore + MemoryManager（scratchpad + 向量检索 + consolidate + compress）
- **产出**：commit `da5a735`
- **测试**：`tests/infrastructure/test_vector_store.py` + `tests/domain/test_memory.py`
- **人工干预**：MemoryManager.read() 只搜索向量存储，遗漏了 scratchpad 中的笔记。agent 添加了 scratchpad 子串匹配
- **教训**：三层存储（scratchpad → 文件 → 向量）的检索需要覆盖所有层

### 记录 2.4 · Task 10-11: 反馈传感器

- **时间**：2026-07-10 11:07（SyntaxSensor）、11:16（TypeCheck + Lint + Test）
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 Sensor ABC + SyntaxSensor + TypeCheckSensor + LintSensor + TestSensor
- **产出**：commits `13ddde0` + `98851ce`
- **测试**：`tests/domain/feedback/test_sensors.py`
- **人工干预**：无
- **教训**：传感器按速度排序（语法→类型→lint→测试）实现快速失败，语法错误时无需等待测试结果

### 记录 2.5 · Task 12: 失败分类器

- **时间**：2026-07-10 11:14
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 FailureClassifier，按 category 和 file_path 聚合失败
- **产出**：commit `1e0c363`
- **测试**：`tests/domain/feedback/test_classifier.py`
- **人工干预**：无
- **教训**：分类器需要同时按类别和文件聚合，以便修正引擎能精确定位问题

### 记录 2.6 · Task 13: 修正策略引擎

- **时间**：2026-07-10 11:08
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 CorrectionEngine，三级策略（RETRY→ROLLBACK→ASK_USER）+ IGNORE 降级
- **产出**：commit `7a5f63a`
- **测试**：`tests/domain/feedback/test_engine.py`
- **人工干预**：无
- **教训**：渐进式升级策略避免死循环，超过最大重试次数自动升级到 ASK_USER

### 记录 2.7 · Task 14: FeedbackPipeline 整合

- **时间**：2026-07-10 11:21
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 FeedbackPipeline，串联 Sensor → Classifier → Engine 全流程
- **产出**：commit `4e84d6f`
- **测试**：`tests/domain/feedback/test_pipeline.py`
- **人工干预**：无
- **教训**：Pipeline 是反馈闭环的核心编排器，将传感器、分类器和修正引擎解耦

---

## Phase 3: 应用层（2026-07-10）

### 记录 3.1 · Task 15: ActionParser

- **时间**：2026-07-10 11:24
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 ActionParser，将 LLMResponse 解析为结构化 Action
- **产出**：commit `91e1f8d`
- **测试**：`tests/application/test_action_parser.py`
- **人工干预**：无
- **教训**：ActionParser 是 LLM 自由文本输出与 harness 结构化动作之间的桥梁

### 记录 3.2 · Task 16: SessionManager

- **时间**：2026-07-10 11:26
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 SessionManager，管理 session 生命周期、步骤记录、JSON 持久化
- **产出**：commit `ad2eacf`
- **测试**：`tests/application/test_session_manager.py`
- **人工干预**：AgentLoop 接口与 PLAN.md 不一致（SessionManager.complete() 签名、SessionManager.record_step() 签名），agent 自行修正
- **教训**：PLAN.md 中的接口签名需要与实际实现保持同步

### 记录 3.3 · Task 17: AgentLoop 主循环

- **时间**：2026-07-10 11:32
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 AgentLoop 主循环，8 个依赖通过依赖注入传入
- **产出**：commit `64dd170`
- **测试**：`tests/application/test_agent_loop.py`
- **人工干预**：AgentLoop 接口与 Governance(tm)、PermissionResult 比较等不匹配，agent 修正了所有接口
- **教训**：依赖注入让 AgentLoop 只依赖接口，便于测试时替换组件

---

## Phase 4: 表示层与集成（2026-07-10）

### 记录 4.1 · Task 18: CLI 入口

- **时间**：2026-07-10 11:36
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 CLI 入口（serve, credentials, run 子命令）
- **产出**：commit `097e3bd`
- **测试**：`tests/test_main.py`
- **人工干预**：无
- **教训**：CLI 是用户与 harness 的第一接触点，需要清晰的子命令结构

### 记录 4.2 · Task 18b: FastAPI 应用

- **时间**：2026-07-10 11:38
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现 FastAPI app + REST routes + WebSocket + credential endpoints
- **产出**：commit `8d6df5e`
- **测试**：`tests/presentation/test_app.py`
- **人工干预**：无
- **教训**：FastAPI 的依赖注入与分层架构天然契合

### 记录 4.3 · Task 19: WebUI 前端

- **时间**：2026-07-10 11:43
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：实现原生 HTML/CSS/JS 前端（6 个面板：任务输入、实时监控、会话历史、审批、凭据管理、日志）
- **产出**：commit `2bebca1`
- **测试**：集成验证（curl 测试所有端点）
- **人工干预**：无
- **教训**：原生前端避免了 React 等框架的依赖，但 UI 交互受限于 DOM 操作

### 记录 4.4 · Task 20: WebUI 集成

- **时间**：2026-07-10 11:49
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：将 SessionManager 注入 WebUI routes，添加 /api/run 和 /api/sessions/{id}/approve 端点
- **产出**：commit `a5dcbc7`
- **测试**：`tests/presentation/test_app.py` 从 3 个扩展到 11 个
- **人工干预**：无
- **教训**：WebUI 集成需要前后端配合，所有端点均通过 curl 集成验证

---

## Phase 5: 机制演示、分发与文档（2026-07-10）

### 记录 5.1 · Task 22-24: 机制演示

- **时间**：2026-07-10 11:36-11:39
- **技能**：`subagent-driven-development`（并行 dispatch）
- **模型**：Sonnet general-purpose agent
- **任务**：
  - Demo 1：治理护栏拦截危险命令，commit `aee2efc`
  - Demo 2：反馈闭环注入语法错误后 agent 修正，commit `e782c6f`
  - Demo 3：完整反馈管线演示，commit `dc69a9f`
- **测试**：`tests/demonstrations/test_demo_*.py`
- **人工干预**：无
- **教训**：三个机制演示均使用 mock LLM 确定性地复现核心行为

### 记录 5.2 · Task 25: Docker + CI

- **时间**：2026-07-10 11:43
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：创建 Dockerfile（Python 3.11-slim）、.gitlab-ci.yml（unit-test job）、conftest.py
- **产出**：commit `ef4bfec`
- **测试**：109 tests passed
- **人工干预**：无
- **教训**：CI 必须包含 `unit-test` job，这是课程硬性要求

### 记录 5.3 · Task 26: README.md

- **时间**：2026-07-10 11:45
- **技能**：`subagent-driven-development`
- **模型**：Sonnet general-purpose agent
- **任务**：创建完整 README.md（安装、运行、凭据配置、安全边界、目录结构、Docker 分发）
- **产出**：commit `5256270`
- **人工干预**：无
- **教训**：README 是用户的第一印象，必须覆盖从零运行到安全配置的完整流程

---

## Phase 6: 部署与最终修复（2026-07-10）

### 记录 6.1 · 跨平台测试修复

- **时间**：2026-07-10 14:00
- **技能**：直接编辑
- **模型**：主对话 Opus
- **任务**：修复 Linux 服务器上 5 个测试失败（3 个 credential_store + 2 个 subprocess）
- **问题**：Linux 无 keyring 后端（需安装 keyrings.alt），`python` 命令不存在（需用 `sys.executable`）
- **产出**：commit `37f7f0b`
- **人工干预**：安装 keyrings.alt 到服务器 venv，修改 `test_subprocess_manager.py` 中的 `"python"` → `f"{sys.executable}"`
- **教训**：跨平台部署需要提前测试，Windows 与 Linux 的命令和库差异会导致非预期失败

### 记录 6.2 · 服务器部署

- **时间**：2026-07-10 14:30
- **技能**：直接操作（SSH + SCP + systemd）
- **模型**：主对话 Opus
- **任务**：部署到阿里云 ECS 服务器 `120.26.110.68`，配置 systemd 服务自动启停
- **关键步骤**：
  1. SCP 传输项目文件到 `/opt/coding-agent/`
  2. 安装 Python 3.11（服务器原装 3.10）
  3. 创建 venv 并安装依赖
  4. 配置 `/etc/systemd/system/coding-agent.service`
  5. 开放安全组端口 8081
- **产出**：服务运行在 `http://120.26.110.68:8081`
- **人工干预**：手动处理 SSH 密钥认证、安全组规则、keyrings.alt 安装
- **教训**：systemd 服务配置需要 `--factory` 标志以支持 FastAPI app factory 模式

### 记录 6.3 · WebUI 根路由修复

- **时间**：2026-07-10 14:45
- **技能**：直接编辑
- **模型**：主对话 Opus
- **任务**：添加 `/` 根路由重定向到 `/static/index.html`
- **产出**：commit `c774253`
- **人工干预**：在 `create_app()` 中添加 `@app.get("/")` 路由
- **教训**：StaticFiles mount 到 `/` 会覆盖根路由，需要 mount 到 `/static` 并添加 RedirectResponse

### 记录 6.4 · Open Design 前端重新设计

- **时间**：2026-07-10 15:00
- **技能**：直接编辑（基于 Open Design 仓库研究）
- **模型**：主对话 Opus
- **任务**：使用 Open Design 的 `linear-app` 设计系统重新设计前端
- **关键步骤**：
  1. 克隆 Open Design 仓库（nexu-io/open-design）
  2. 阅读 `design-systems/linear-app/DESIGN.md`（9 节完整规范）
  3. 提取 `design-systems/linear-app/tokens.css`（56 个 CSS 自定义属性）
  4. 对照 `design-systems/linear-app/components.manifest.json` 确认组件
  5. 完全重写 `DESIGN.md`、`style.css`、`index.html`、`app.js`
- **产出**：commits `98b324d` + `c83de98`
- **人工干预**：全部手写，因前端重设计需要精确匹配 Linear 设计令牌
- **教训**：Open Design 不是 CSS 框架，是一套设计方法论——DESIGN.md + tokens.css + SKILL.md 驱动制品生成

### 记录 6.5 · 过程文档与反思

- **时间**：2026-07-10 15:30
- **技能**：直接编辑
- **模型**：主对话 Opus
- **任务**：创建 AGENT_LOG.md 和 REFLECTION.md
- **产出**：commit `4b5a9ad`
- **人工干预**：全部手写，反思报告需个人撰写
- **教训**：过程文档是 agentic 工程中最重要的证据，记录了每个决策和修正

---

## Phase 7: 第二轮审计与修复（2026-07-10）

### 记录 7.1 · 第二次综合审计

- **时间**：2026-07-10 16:00
- **技能**：直接操作 + 3 个并行 Explore subagent
- **模型**：主对话 Opus + 3 个 Sonnet Explore agent
- **任务**：对照课程文档和项目产出做第二轮全面审计
- **Agent 1**：从课程文档提取 109 条检查项（L01-L07, SEC01-SEC11, DIST01-DIST13, TECH01-03, SIZE01-05, TOOL01-09, SPECPLAN01-03, SPEC01-11, PLAN01-03, SPRO01-04, COLD01-06, IMPL01-07, GIT01-07, TEST01-04, LOG01-07, CLOUD01-04, DEL01-10, REFL01-09, ACAD01-03, HARN01-23）
- **Agent 2**：文档一致性检查，发现 12 个问题（C1-C2, M1-M5, m1-m6）
- **Agent 3**：源代码 vs SPEC 验证，发现 10 个偏差（#1-#10）
- **综合结论**：17 个问题（3 CRITICAL + 7 MAJOR + 7 MINOR）
- **人工干预**：用户确认修复全部 17 个问题

### 记录 7.2 · 修复 17 个审计问题

- **时间**：2026-07-10 16:30
- **技能**：直接编辑
- **模型**：主对话 Opus
- **任务**：修复全部 17 个审计发现的问题
- **关键修复**：
  1. C1: 新增 `real_llm.py`，实现 OpenAI-compatible `RealLLMProvider`
  2. C2: `agent_loop.py` 新增 `_call_llm()` 方法，含 3 次重试 + 120s 超时
  3. C3: `governance.py` 新增 `HITLState.is_expired()` 方法，5 分钟超时
  4. M1: `pipeline.py` 改用 `ThreadPoolExecutor` 并行执行 sensor
  5. M2: `engine.py` 修改 `decide()` 逻辑，RETRY → ROLLBACK → ASK_USER 三级渐进
  6. M3: PLAN.md 移除不存在的文件引用（git_ops.py、test_git_ops.py 等）
  7. M4: AGENT_LOG.md 和 REFLECTION.md 的 commit 数修正为 35
  8. M5: 新增 `.git/hooks/pre-commit` 扫描 API key 和敏感文件
  9. M6: 新增 `AGENTS.md` 补充规则文件
  10. M7: SPEC.md 中 DESIGN.md 路径修正为 `coding_agent/presentation/static/DESIGN.md`
  11. m1: `models.py` StepRecord 新增 llm_response、governance_result、feedback_report 字段
  12. m2: `governance.py` 新增 `set_tool_permissions()` 方法，支持从 ToolManager 同步权限
  13. m3: Makefile `clean` 改用 Python 跨平台实现
  14. m4: Dockerfile 恢复为生产镜像（移除 dev 依赖和测试文件）
  15. m5: `.gitlab-ci.yml` 改用 `pip install -e ".[dev]"`
  16. m6: SPEC.md 新增 9.4 测试策略章节
  17. m7: AGENT_LOG.md 补充 CLAUDE.md 创建记录
- **测试**：109/109 passed
- **人工干预**：全部手写，因涉及多文件协调修改

### 记录 7.3 · 补充 CLAUDE.md 创建记录

- **时间**：2026-07-10 10:30（补记）
- **技能**：`writing-plans`
- **模型**：主对话 Opus
- **任务**：在 writing-plans 阶段同时创建了 CLAUDE.md 项目级 agent 章程
- **产出**：commit `01d7e81`（与 PLAN.md 初始版本同 commit）
- **教训**：AGENT_LOG 应记录所有过程性产出，不仅是代码实现

---

## 总结统计

| 指标 | 数值 |
|------|------|
| 总 commit 数 | 42 |
| 总 task 数 | 26（按 PLAN.md） |
| 使用的 subagent 数 | ~20（Sonnet general-purpose） |
| 总测试数 | 109 |
| 测试通过率 | 100%（109/109 passed） |
| 机制演示 | 3（治理拦截、反馈修正、完整管线） |
| 部署环境 | 阿里云 ECS + systemd |
| 人工干预次数 | 8（build-backend 修正、PLAN.md 修订、governance 测试修正、memory 检索修正、跨平台修复、前端重设计、服务器部署、第二轮审计修复） |

### 关键教训总结

1. **冷启动验证是硬性门禁**：陌生 agent 发现了人类 review 容易忽略的错误（无效 build-backend）
2. **PLAN.md 接口签名必须与实际一致**：AgentLoop 的多个接口与 PLAN.md 不匹配，agent 自行修正
3. **平台差异不可忽视**：`mkdir -p` vs `New-Item`、`python` vs `python3`、keyring vs keyrings.alt
4. **TDD 纪律确保可测试性**：109 个测试全部使用 mock LLM，无需真实 API key
5. **subagent-driven 模式有效**：每个 task 由独立 Sonnet agent 执行，减少了上下文污染
6. **依赖注入是测试的关键**：AgentLoop 的所有依赖通过接口注入，便于 mock 替换
7. **Open Design 不是 CSS 框架**：需要 clone 实际仓库、阅读设计系统源码、使用真实令牌
8. **服务器部署需要提前规划**：Python 版本、keyring 后端、安全组规则都是潜在阻塞点
9. **多轮审计是质量保障**：第二次审计发现 17 个问题，其中 3 个 CRITICAL 级别（真实 LLM provider 缺失、LLM 重试/超时未实现、HITL 超时未实现），这些问题在第一次审计中被遗漏
## Phase 7: 作业合规修复与终验（2026-07-11）

### 记录 7.1 · 独立 worktree 修复

- **工具**：OpenAI Codex CLI + Superpowers
- **分支**：`fix/assignment-compliance`，worktree 为 `.worktrees/assignment-compliance-fix`
- **问题**：真实组合根遗漏 `FileSystemManager` / `SubprocessManager` 注入，导致 `coding-agent serve` 与 `run` 初始化失败；ruff 与 mypy strict 未通过
- **TDD**：先新增 `_create_agent_loop()` 回归测试并观察 `TypeError`，再补依赖注入使测试转绿
- **修复**：补齐 strict 类型契约、WebUI session 复用、`write_file` 变更文件回灌、`allowed_dirs` 前缀逃逸、FastAPI lifespan、wheel 静态资源、容器 secret 文件凭据来源

### 记录 7.2 · 最终质量门禁

- **ruff**：`ruff check coding_agent/ tests/` 通过
- **mypy**：`mypy coding_agent/` strict 模式通过，34 个源文件零错误
- **测试**：115/115 passed，并以 `DeprecationWarning` 作为 error 验证输出干净
- **分发**：sdist/wheel 构建成功；在独立 venv 安装 wheel 后 `coding-agent --help` 可运行，WebUI 静态资源存在于 site-packages
- **Docker**：CI 已配置镜像构建；本机未安装 Docker CLI，需以最终远端 CI 成功记录作为提交证据
- **人工判断**：没有把“单测通过”当成真实入口可用的替代证据，增加组合根、WebUI session 和分发烟测
