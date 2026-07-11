# SPEC.md · Coding Agent Harness

> **Agent = LLM × Harness**。LLM 只负责"下一步做什么"这一行任务决策，其余全是工程。
> 本项目从零实现一个 Coding Agent Harness，让 LLM 能稳定、安全、可靠地完成编码任务。

---

## 一、问题陈述

### 要解决的问题

大语言模型（LLM）能产生代码设想，但单靠 LLM 本身无法稳定完成编码工作——它缺乏工具调用、记忆、安全护栏、客观反馈和声明式约束。现有 agent 框架（LangChain、AutoGen、CrewAI 等）提供了高层编排，但开发者若直接使用它们，等于把自己的核心机制寄托于黑盒框架。

本项目要交付一个**自己编码实现的 Coding Agent Harness 内核**，将 LLM 从"会思考的芯片"变成"能工作的计算机"。harness 提供工具、记忆、治理、反馈和配置，让 LLM 在编码场景中可靠运行。

### 目标用户

- 希望理解 agent 工程原理的软件工程学生和研究者
- 需要可审计、可定制 coding agent 的开发者
- 对 agent 安全性和可观测性有要求的团队

### 为什么值得做

1. **教育价值**：亲手实现 harness 才能理解 agent 工程的每个环节，而不是"调包了事"
2. **工程深度**：六个维度（决策/工具/记忆/治理/反馈/配置）都要有代码实现，不是写 prompt
3. **可审计性**：每个机制都可用 mock LLM 做确定性测试，不依赖真实 LLM 的"智能"
4. **安全性**：治理护栏和反馈闭环是代码机制，不是提示词建议

---

## 二、用户故事（INVEST）

### US1: 作为开发者，我可以向 agent 提交编码任务并获得结果
- **描述**：通过 CLI 或 WebUI 输入任务描述（如"在 src/utils.py 中添加一个 `parse_date` 函数"），agent 自动完成编码并返回结果
- **验收**：输入任务后，agent 在步数限制内完成或报告失败，过程可追踪

### US2: 作为开发者，我可以安全配置 API key 而不用担心泄露
- **描述**：首次运行时通过安全方式录入 LLM API key，可查看状态（不显示明文）、更新和清除
- **验收**：key 存储在 Windows Credential Manager 中，不进入 Git、日志、终端 history

### US3: 作为开发者，我可以信任 agent 不会执行危险操作
- **描述**：agent 在执行危险命令前被拦截，需要我确认或审批；极度危险的命令（如 `rm -rf /`）直接阻止
- **验收**：构造危险动作，确认被护栏拦截；普通操作正常放行

### US4: 作为开发者，我可以看到 agent 根据测试失败自动修正代码
- **描述**：agent 修改代码后自动运行测试/lint/类型检查，如果失败，反馈信息注入上下文，agent 据此修正
- **验收**：注入一次失败，确认 agent 在下一轮中尝试修正，修正后测试通过

### US5: 作为开发者，我可以通过配置文件约束 agent 的行为
- **描述**：在项目目录放置 `CLAUDE.md` 或 `config.yaml`，声明代码风格、禁改目录、步数上限等约束
- **验收**：修改配置后，agent 行为随之改变（如禁止修改某目录）

### US6: 作为开发者，我可以查看历史会话和 agent 的决策轨迹
- **描述**：WebUI 中浏览历史会话，查看每一步的 LLM 决策、工具调用、反馈结果
- **验收**：完成一次会话后，在 WebUI 历史面板中看到完整轨迹

### US7: 作为开发者，我可以通过 Docker 一键运行整个系统
- **描述**：`docker build && docker run` 后，WebUI 可访问，输入 API key 即可开始使用
- **验收**：在全新机器上按 README 步骤操作，WebUI 成功启动

---

## 三、功能规约

### 3.1 决策封装（应用层）

| 项目 | 内容 |
|------|------|
| **输入** | 任务目标（goal）、已装配的 harness 组件 |
| **行为** | 组织上下文 → 调用 LLM → 解析动作 → 分发执行 → 回灌结果 → 判断停机 |
| **输出** | `AgentResult(success, answer)` |
| **边界条件** | 步数超过 `max_steps` 时强制停机；上下文过长时触发压缩 |
| **错误处理** | LLM 调用失败时重试（最多 3 次），超时则终止会话 |

**LLM 抽象接口**：`LLMProvider.chat(messages, tools) → LLMResponse`，真实实现和 mock 实现均遵循此接口。mock 分两种：`ScriptedMockLLM`（预设响应序列）和 `RuleBasedMockLLM`（模式匹配响应）。

### 3.2 工具/动作（领域层）

| 项目 | 内容 |
|------|------|
| **输入** | `Action` 对象（type, tool_name, tool_args） |
| **行为** | 根据 action.type 分发：CALL_TOOL → 查找工具 → 执行 → 返回结果；DONE → 标记完成；TAKE_NOTE → 写入记忆 |
| **输出** | `ActionResult(success, output, error, changed_files)` |
| **边界条件** | 工具名不存在时返回错误；工具执行超时（默认 120s）时终止 |
| **错误处理** | 工具执行异常被捕获并回灌给 LLM，不中断主循环 |

**内置工具**：`read_file`(SAFE)、`write_file`(RISKY)、`list_dir`(SAFE)、`search_files`(SAFE)、`grep`(SAFE)、`run_shell`(DANGEROUS)、`run_test`(SAFE)、`git_status`(SAFE)、`git_diff`(SAFE)、`git_commit`(RISKY)

### 3.3 上下文与记忆（领域层）

| 项目 | 内容 |
|------|------|
| **输入** | 任务目标、历史消息、记忆存储 |
| **行为** | 装配初始上下文（系统提示 + 规则 + 记忆检索 + 目标）；循环内即时写笔记；会话末固化长期记忆；上下文超长时压缩 |
| **输出** | 每轮组装好的 `messages` 列表 |
| **边界条件** | 记忆检索 top-K 默认 5 条；上下文 token 上限默认 8000 |
| **错误处理** | 向量检索失败时降级为关键词匹配；压缩失败时截断旧消息 |

**存储层次**：会话内 scratchpad（内存）→ 长期记忆文件（JSON）→ 向量索引（InMemoryVectorStore，哈希嵌入 + 余弦相似度检索）

### 3.4 治理护栏（领域层）

| 项目 | 内容 |
|------|------|
| **输入** | `Action` 对象 |
| **行为** | 检查工具权限级别：SAFE 放行、RISKY 需确认、DANGEROUS 需 HITL；额外检查危险命令模式（直接 BLOCKED） |
| **输出** | `PermissionResult(ALLOWED/BLOCKED/NEEDS_CONFIRMATION/NEEDS_HITL)` |
| **边界条件** | HITL 审批超时（默认 5 分钟）视为拒绝 |
| **错误处理** | 治理模块自身异常时默认 BLOCKED（安全优先） |

**危险命令模式**（硬拦截，不可 HITL 放行）：`rm -rf /`、`DROP TABLE`、`git push --force main`、`chmod 777 /`、`format C:` 等

### 3.5 反馈闭环（领域层 · 主贡献）

| 项目 | 内容 |
|------|------|
| **输入** | 变更文件列表 `changed_files` |
| **行为** | Sensor 管线（语法→类型→lint→测试）→ 失败分类器（按类别+文件聚合）→ 修正策略引擎（决定重试/回退/升级）→ 结构化反馈文本注入上下文 |
| **输出** | 反馈摘要文本，注入 `context` |
| **边界条件** | 无变更文件时跳过；单轮修正最多 3 次；修正总轮次不超过 `max_retries` |
| **错误处理** | Sensor 执行失败时报告为 UNKNOWN 类别，不阻塞主循环 |

**Sensor 管线**：
1. `SyntaxSensor`（`py_compile`，最快）
2. `TypeCheckSensor`（mypy/pyright）
3. `LintSensor`（ruff）
4. `TestSensor`（pytest）

**失败分类**：SYNTAX_ERROR / TYPE_ERROR / TEST_FAILURE / LINT_WARNING / IMPORT_ERROR / TIMEOUT / UNKNOWN

**修正策略**：RETRY（附带错误信息重试）→ ROLLBACK（回退变更）→ ASK_USER（升级给用户）

### 3.6 配置（领域层）

| 项目 | 内容 |
|------|------|
| **输入** | 项目目录路径 |
| **行为** | 加载 `config.yaml`（默认值）→ `CLAUDE.md`（项目规则）→ `AGENTS.md`（补充规则）→ 环境变量覆盖 |
| **输出** | `Config` 对象 |
| **边界条件** | 所有配置项有默认值，无配置文件也可运行 |
| **错误处理** | 配置文件格式错误时报告并跳过，使用默认值 |

---

## 四、非功能性需求

### 4.1 性能
- 主循环单步延迟（不含 LLM 调用）：< 100ms
- Sensor 管线总耗时（不含测试）：< 30s
- WebUI 页面加载：< 2s

### 4.2 安全（含凭据威胁模型）

**威胁模型**：
| 威胁 | 风险等级 | 对策 |
|------|----------|------|
| API key 泄露到 Git | 高 | `.gitignore` 排除 `.env`、`credentials`、secret 文件与日志；提交前执行凭据扫描 |
| API key 泄露到日志 | 高 | 日志系统自动脱敏，替换 key 为 `****` |
| API key 在进程列表中可见 | 中 | 不通过命令行传 key，通过 Credential Manager 或安全输入 |
| 恶意 prompt 注入 | 中 | 危险命令模式匹配 + 权限分级，不依赖 LLM 自我约束 |
| `.env` 明文存储 | 中 | 支持 `.env` 作为输入源，但 README 说明风险，推荐 Credential Manager |
| 未授权文件访问 | 中 | `allowed_dirs` 配置限定工作目录范围 |

**凭据安全存储**：本机使用操作系统凭据管理器（`keyring` 库）；Docker 使用只读 secret 文件挂载，并通过 `CODING_AGENT_API_KEY_FILE` 指定路径。key 不写入镜像、项目配置或日志。

**凭据生命周期**：
- 录入：`coding-agent credentials set`（隐藏输入）
- 查看状态：`coding-agent credentials status`（只显示是否已配置，不显示明文）
- 更新：`coding-agent credentials set`（覆盖）
- 清除：`coding-agent credentials clear`

### 4.3 可用性
- 首次运行引导用户录入 API key
- CLI 命令有清晰的 help 文本
- WebUI 有直观的任务输入和审批流程
- 错误信息包含可操作的提示

### 4.4 可观测性
- 每步决策记录到轨迹（`sessions/` 目录下 JSON 文件）
- WebUI 实时展示执行步骤
- Tracer 记录（决策, 观察）对，可回放

---

## 五、系统架构

### 5.1 分层架构

```
┌─────────────────────────────────────────────────────┐
│                    表示层 (Presentation)              │
│  FastAPI + WebSocket + 静态前端                       │
│  REST API: /api/run, /api/approve, /api/status, ...  │
├─────────────────────────────────────────────────────┤
│                    应用层 (Application)               │
│  AgentLoop: 主循环编排                                │
│  SessionManager: 会话生命周期                         │
│  ActionParser: LLM 输出 → 结构化 Action               │
├─────────────────────────────────────────────────────┤
│                    领域层 (Domain)                    │
│  ToolManager │ Governance │ FeedbackPipeline │ Memory │
│  工具注册分发 │ 三级权限    │ Sensor管线       │ 向量检索│
│              │ HITL审批   │ 失败分类         │ 压缩固化│
│  Config: 声明式配置加载                               │
├─────────────────────────────────────────────────────┤
│                  基础设施层 (Infrastructure)          │
│  LLMProvider │ CredentialStore │ VectorStore(InMemory) │
│  FileSystem  │ GitOps          │ SubprocessManager   │
└─────────────────────────────────────────────────────┘
```

**调用规则**：上层可调用下层，下层不依赖上层。应用层通过依赖注入获取领域层组件，领域层通过接口依赖基础设施层。

### 5.2 组件图

```
                    ┌──────────────┐
                    │   WebUI      │
                    │ (FastAPI+WS) │
                    └──────┬───────┘
                           │ REST/WS
                    ┌──────▼───────┐
                    │  AgentLoop   │
                    │  (主循环)     │
                    └──┬───┬───┬──┘
                       │   │   │
          ┌────────────┼───┼───┼────────────┐
          │            │   │   │            │
    ┌─────▼─────┐ ┌───▼───▼───▼───┐ ┌─────▼─────┐
    │ToolManager│ │FeedbackPipeline│ │ Governance│
    │ 工具分发   │ │ Sensor→分类→策略│ │ 护栏+审批 │
    └─────┬─────┘ └───────┬───────┘ └─────┬─────┘
          │               │               │
    ┌─────▼─────┐ ┌───────▼───────┐ ┌─────▼─────┐
    │Subprocess │ │  TestRunner   │ │ MemoryMgr │
    │ GitOps    │ │  LintRunner   │ │ Config    │
    └───────────┘ └───────────────┘ └───────────┘
```

### 5.3 数据流（一轮循环）

```
1. [Memory + Config] → 组装 context
2. context → [LLMProvider] → text + action
3. action → [Governance.check] → ALLOWED/BLOCKED/CONFIRM/HITL
4. action → [ToolManager.dispatch] → ActionResult
5. ActionResult.changed_files → [FeedbackPipeline.run] → feedback text
6. feedback text → context (回灌)
7. → 下一轮循环 或 DONE → 返回
```

### 5.4 外部依赖

- **LLM 供应商**：OpenAI 兼容 API（GPT-4o / Claude / DeepSeek 等均可）
- **InMemoryVectorStore**：内存向量存储，哈希嵌入 + 余弦相似度，无外部服务依赖
- **keyring**：跨平台凭据存储库
- **FastAPI + uvicorn**：Web 服务
- **pytest / ruff / mypy**：反馈传感器的检测工具（在项目工作区中运行）

---

## 六、数据模型

### 6.1 核心实体

```
Message
├── role: "system" | "user" | "assistant"
├── content: str
└── tool_calls: list[ToolCall] | None

Action
├── type: CALL_TOOL | DONE | TAKE_NOTE
├── tool_name: str | None
├── tool_args: dict | None
├── thought: str
└── note: str | None

ActionResult
├── success: bool
├── output: str
├── error: str | None
└── changed_files: list[str]

SensorReport
├── sensor_name: str
├── passed: bool
├── failures: list[SensorFailure]
└── duration_ms: int

SensorFailure
├── file_path: str
├── line: int | None
├── severity: ERROR | WARNING
├── category: FailureCategory
├── message: str
└── raw_output: str

MemoryEntry
├── id: str (UUID)
├── content: str
├── embedding: list[float] | None
├── timestamp: datetime
├── type: "scratchpad" | "long_term"
└── tags: list[str]

Session
├── id: str (UUID)
├── goal: str
├── start_time: datetime
├── end_time: datetime | None
├── steps: list[StepRecord]
├── result: AgentResult | None
└── status: RUNNING | COMPLETED | FAILED | CANCELLED

StepRecord
├── step_number: int
├── llm_response: LLMResponse | None
├── action: Action | None
├── action_result: ActionResult | None
├── governance_result: PermissionResult | None
├── feedback_report: ClassifiedResult | None
└── timestamp: datetime

Config
├── max_steps: int (default 50)
├── max_context_tokens: int (default 8000)
├── max_retries: int (default 3)
├── allowed_dirs: list[str] (default ["."])
├── blocked_patterns: list[str]
├── model_name: str
├── tools_enabled: list[str]
└── sensor_pipeline: list[str] (default ["syntax", "typecheck", "lint", "test"])
```

### 6.2 关系与约束

- 一个 `Session` 包含多个 `StepRecord`
- 一个 `StepRecord` 关联一个 `Action` 和一个 `ActionResult`
- 一个 `ActionResult` 触发一个 `FeedbackPipeline` 运行，产生多个 `SensorReport`
- `MemoryEntry` 属于一个项目（通过 project_id 关联）
- `Config` 按项目加载，全局默认值在 `~/.coding-agent/config.yaml`

---

## 七、凭据与分发设计

### 7.1 凭据存储方案

**首选**：Windows Credential Manager（通过 `keyring` 库）
- 加密存储，由操作系统管理
- 不落地明文文件
- 跨平台兼容（macOS Keychain / Linux Secret Service）；不使用明文 fallback keyring

**备选**：`.env` 文件
- 明文存储，风险高
- 仅作为开发时的便捷输入源
- `.gitignore` 必须排除
- README 必须说明风险

### 7.2 凭据操作

```
coding-agent credentials set       # 隐藏输入 API key
coding-agent credentials status    # 查看状态（不显示明文）
coding-agent credentials clear     # 清除 API key
```

### 7.3 分发形态

**Docker 镜像**（主要）：
```bash
docker build -t coding-agent .
docker run -p 8080:8080 -v ~/.coding-agent:/root/.coding-agent coding-agent
```

**PyPI 包**（补充）：
```bash
pip install coding-agent-harness
coding-agent serve --port 8080
```

### 7.4 目标平台

- 开发：Windows 11（Python 3.11+）
- 部署：Docker（Linux x86_64）
- 测试：Windows / Linux

---

## 八、技术选型与理由

| 技术 | 用途 | 理由 |
|------|------|------|
| **Python 3.11+** | 主语言 | 快速原型、丰富生态、课程教学友好 |
| **FastAPI** | Web 框架 | 高性能异步、原生 WebSocket、自动 OpenAPI 文档 |
| **Pydantic** | 数据模型 | 类型安全、自动校验、与 FastAPI 深度集成 |
| **keyring** | 凭据存储 | 跨平台、操作系统原生加密 |
| **InMemoryVectorStore** | 向量存储 | 内存运行、哈希嵌入、Python 原生、无需外部服务 |
| **OpenAI SDK** | LLM 调用 | 兼容协议最广泛，可接任意供应商 |
| **pytest** | 测试框架 | Python 生态标准，也是反馈 sensor 的检测工具 |
| **ruff** | Lint sensor | 极快、Python 原生、替代 flake8 |
| **mypy** | 类型检查 | Python 静态类型标准工具 |
| **Docker** | 分发 | 环境一致、一键运行、课程要求 |
| **原生 HTML/CSS/JS + Open Design** | 前端 | 无框架依赖、轻量、易于打包。使用 Open Design 的 `linear-app` 设计系统（Linear-inspired dark-mode-first），`prototype` skill 生成界面。设计令牌源自 `design-systems/linear-app/tokens.css`，详见 `coding_agent/presentation/static/DESIGN.md` |

---

## 九、领域与机制设计（A 类额外要求）

### 9.1 领域分析

**领域**：Coding——软件开发场景中的代码阅读、编写、修改、测试。

**反馈信号**：
- 测试结果（pass/fail + 断言差异）
- 类型检查错误（mypy/pyright 输出）
- Lint 警告（ruff 输出）
- 语法错误（py_compile 输出）
- Shell 命令执行结果（exit code + stdout/stderr）

**危险动作**：
- 删除关键文件（`rm -rf`、`del /f`）
- 数据库破坏性操作（`DROP TABLE`、`DELETE FROM`）
- 强制推送到主分支（`git push --force main`）
- 系统级权限变更（`chmod 777 /`）
- 对外发布（`pip publish`、`docker push`、`git push`）

**所需工具**：文件读写、shell 命令执行、文件搜索、内容搜索、git 操作、测试运行

**记忆需求**：项目约定（CLAUDE.md）、历史决策记录、代码库结构知识、会话内笔记

### 9.2 重点维度：反馈闭环

**选择理由**：
1. Coding 场景中反馈信号最客观、最确定（测试通过/失败、类型正确/错误），天然适合编码成机制
2. 反馈闭环是"agent 自我修正"的核心——没有反馈，agent 只能盲目尝试
3. 多层 sensor 管线 + 失败分类 + 差异化策略，深度足够
4. 每个组件（Sensor、Classifier、Engine）都可用 mock LLM 做确定性测试

**实现方式**：
- Sensor 管线：异步并行运行多个 sensor，按速度排序（语法 → 类型 → lint → 测试）
- 失败分类器：解析 sensor 原始输出，提取结构化字段，按类别和文件聚合
- 修正策略引擎：基于失败类别和重试次数决定策略（RETRY/ROLLBACK/ASK_USER）
- 反馈文本生成：按优先级排序失败列表，生成清晰的结构化摘要注入上下文

### 9.3 机制可单测性验证

每个核心机制都满足"移除真实 LLM 后仍可用确定性单元测试验证"：

| 机制 | 测试方式 | 不依赖 |
|------|----------|--------|
| 主循环 | 注入 ScriptedMockLLM，断言步数、动作分发、停机 | 真实 LLM |
| 工具分发 | 构造 Action 对象，断言工具查找、参数传递、结果格式 | 真实 LLM |
| 治理护栏 | 构造 Action 对象，断言 PermissionResult | 真实 LLM |
| 反馈管线 | 构造变更文件（含故意错误），断言 Sensor 检测、分类、策略 | 真实 LLM |
| 记忆读写 | 写入/检索 MemoryEntry，断言检索结果 | 真实 LLM |
| 配置加载 | 加载 fixture 配置文件，断言 Config 字段值 | 真实 LLM |

### 9.4 测试策略

**分层测试原则**：

| 测试层 | 范围 | mock 策略 | fixture |
|--------|------|-----------|---------|
| 单元测试 | 单个类/函数 | Mock LLM (ScriptedMockLLM / RuleBasedMockLLM) | `conftest.py` 中的共享 fixture |
| 集成测试 | 跨模块交互 | Mock LLM + 真实工具分发 | 临时目录 + git init |
| 机制演示 | 端到端场景 | ScriptedMockLLM 预设对话序列 | 临时项目目录 + 故意错误文件 |

**核心原则**：移除真实 LLM 后，所有核心机制仍可用确定性单元测试验证。测试不依赖网络、不依赖真实 API key。

**TDD 纪律**：先写失败测试（红灯）→ 确认失败原因 → 写最小实现（绿灯）→ 重构（保持绿灯）。

---

## 十、验收标准

### 功能验收

- [x] 用户通过 CLI 或 WebUI 提交编码任务，agent 在步数限制内完成或报告失败
- [x] API key 安全录入、查看状态、更新、清除流程完整可用
- [x] 危险动作被护栏拦截（硬拦截不可绕过，软拦截需审批）
- [x] 代码变更后自动运行反馈管线，失败信息回灌并驱动修正
- [x] 配置文件（CLAUDE.md / config.yaml）的约束生效
- [x] 历史会话轨迹可浏览、可回放

### 机制演示验收

- [x] 演示 1：治理护栏拦截一个危险动作（mock LLM 驱动）
- [x] 演示 2：注入一次测试失败，反馈闭环使 agent 收到反馈并修正（mock LLM 驱动）
- [x] 演示 3：反馈闭环的完整管线——sensor → 分类 → 策略 → 回灌（主贡献维度）

### 测试验收

- [x] 一键测试命令 `make test` 或 `pytest` 全部通过
- [x] 核心机制 mock-LLM 单元测试覆盖
- [x] `.gitlab-ci.yml` 包含 `unit-test` job

### 分发验收

- [x] Docker 镜像可构建、可运行
- [x] README 完整（获取、安装、运行、key 配置、已知限制、目录结构、安全边界）

### 文档验收

- [x] SPEC.md / PLAN.md / SPEC_PROCESS.md / AGENT_LOG.md / README.md / REFLECTION.md 均存在
- [x] 文档内容与代码实现一致
- [x] REFLECTION.md 1500-2500 字

---

## 十一、风险与未决问题

### 已识别风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| subprocess 执行安全性 | 高 | 治理护栏 + allowed_dirs 限定 + 超时控制 |
| 上下文窗口溢出 | 中 | 压缩机制 + token 计数 + 步数限制 |
| 反馈循环死循环 | 中 | max_retries 上限 + ASK_USER 升级策略 |
| 嵌入方法选择 | 低 | 默认使用 SHA-256 哈希嵌入，可扩展为其他嵌入方法 |
| WebSocket 连接不稳定 | 低 | 自动重连 + 降级为轮询 |
| 真实 LLM 费用 | 低 | mock LLM 开发测试，真实 LLM 仅在演示时使用 |

### 未决问题

1. **嵌入方法选择**：当前使用 SHA-256 哈希嵌入 + 余弦相似度检索，适用于中小规模项目。如需语义搜索，可扩展为 sentence-transformers 等语义嵌入模型。
2. **Windows Credential Manager 的跨平台测试**：开发环境为 Windows，但 Docker 部署在 Linux。keyring 在 Linux 上使用 Secret Service，需验证 Docker 环境中的行为。
3. **WebUI 前端是否需要框架**：当前设计为原生 HTML/CSS/JS。如果交互复杂度超出预期，是否需要引入轻量框架（如 Alpine.js）？
4. **多项目会话隔离**：同一用户在不同项目中运行 agent 时，记忆和配置如何隔离？当前设计为按项目目录区分，但需确认细节。
