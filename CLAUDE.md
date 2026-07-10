# CLAUDE.md

本文件是本项目的项目级 agent 操作章程。任何参与本仓库的 Claude Code、Codex、Cursor Agent、Gemini CLI、Copilot CLI 或其它编码智能体，必须先阅读并遵守本文件，再执行任务。

本项目默认选择期末项目 **A · Coding Agent Harness**。完整要求由以下文档共同构成：

- `docs/AI4SE_Final_Project_通用要求.md`
- `docs/AI4SE_Final_Project_A_Coding_Agent_Harness.md`
- `docs/Agent 的一生 · 一段伪代码看懂全过程.html`
- `docs/AgenticEngineering-with-notes.pptx`
- `docs/pecehe-with-notes.pptx`
- `docs/如何成为智能化软件工程师.pdf`

如本文件与课程原始文档冲突，以课程原始文档为准；如本文件与用户直接指令冲突，先指出冲突并等待确认，不要静默选择。

## 语言与沟通

- 与用户对话、编写文档、计划、日志和总结时默认使用中文。
- 技术名词、代码/API 名称、命令、文件路径、错误信息、协议名和项目既有英文术语可以保留英文。
- 不确定时明确说出不确定点、可选解释和风险，不要假装已经理解。
- 所有结论都要尽量落到文件、测试、命令、课程文档或可验证事实上。

## 项目核心理解

本项目不是普通应用开发，也不是为现成 agent 框架写配置。项目目标是使用 Superpowers 所代表的 agentic engineering 流程，交付一个**自己编码实现的 Coding Agent Harness**，并对它的工程过程、可信性、安全性、分发和反思负责。

核心公式：

```text
Agent = LLM × Harness
```

LLM 只负责基于上下文做下一步任务决策；harness 负责让它能稳定工作，包括工具、上下文、记忆、治理、反馈、配置、可观测性和分发。

本项目要训练的问题是：当 LLM 能完成大量编码时，工程师如何通过规约、计划、测试、评审、安全边界和反馈机制来判断“做什么”和“做对了吗”。

## 绝对流程门禁

在 `SPEC.md`、`PLAN.md` 完成并通过冷启动验证之前，禁止编写任何实现代码、搭建业务源码、创建核心模块或补测试。

允许在此阶段做的事情：

- 阅读、整理和引用现有文档。
- 产出或修订 `SPEC.md`、`PLAN.md`、`SPEC_PROCESS.md`、`AGENT_LOG.md`、`README.md` 草稿等过程文档。
- 设计技术方案、架构图、数据模型、测试策略和分发策略。
- 创建不含实现逻辑的目录规划说明。

禁止在此阶段做的事情：

- 创建 harness 内核实现文件。
- 编写真实工具分发、agent loop、LLM 调用、guardrail、memory、feedback sensor 等实现代码。
- 先写实现再补 spec 或 plan。
- 为了“探路”写临时代码后保留在仓库中。

如果用户要求跳过流程，必须提醒课程要求：`brainstorming → writing-plans → cold-start validation → implementation` 是硬性过程证据。除非用户明确要求偏离，并要求写入 `AGENT_LOG.md` 解释原因，否则不要跳过。

## Superpowers 工作流

必须如实遵循并记录 Superpowers 七步工作流：

1. `brainstorming`：从模糊想法形成可审查的设计。
2. `writing-plans`：把设计拆成 2-5 分钟粒度、含验证步骤的任务。
3. `using-git-worktrees`：为独立功能或大模块隔离工作区。
4. `subagent-driven-development` 或 `executing-plans`：用新鲜 subagent 执行单一任务。
5. `test-driven-development`：红、绿、重构。
6. `requesting-code-review`：先 spec 合规检查，再代码质量检查。
7. `finishing-a-development-branch`：决定 merge、PR、保留或丢弃。

任何偏离都必须记录到 `AGENT_LOG.md`，包括时间、任务编号、偏离原因、风险和补救措施。

## 必交文档

必须维护以下文件。除非用户明确指定其它位置，均放在仓库根目录。

- `SPEC.md`：设计文档。
- `PLAN.md`：实现计划。
- `SPEC_PROCESS.md`：spec/plan 生成与冷启动验证过程。
- `AGENT_LOG.md`：agent 协作日志。
- `README.md`：项目简介、安装、运行、分发命令、目录结构、安全边界说明。
- `REFLECTION.md`：1500-2500 字个人反思报告。
- `.gitlab-ci.yml`：CI 配置，必须包含名为 `unit-test` 的 job。

`SPEC.md` 必须覆盖：

- 问题陈述、目标用户、为何值得做。
- 至少 5 个 INVEST 用户故事。
- 按模块拆分的功能规约：输入、行为、输出、边界条件、错误处理。
- 非功能需求：性能、安全、可用性、可观测性。
- 系统架构、组件图、数据流、外部依赖。
- 数据模型：实体、字段、关系、约束。
- 凭据与分发设计。
- 技术选型与理由。
- 验收标准。
- 风险与未决问题。
- A 类项目额外要求的「领域与机制设计」。

`PLAN.md` 必须覆盖：

- 每个 task 的目标、涉及文件、实现要点和验证步骤。
- 每个 task 将要先写的失败测试。
- task 间依赖关系和可并行部分。
- 每完成一个 task，标记完成并附 commit hash。

`SPEC_PROCESS.md` 必须覆盖：

- brainstorming 关键节点。
- 至少 3 轮关键迭代的对话节选和处理决策。
- AI 建议中采纳、推翻、修正的部分及理由。
- 使用不同类型陌生 agent 进行冷启动验证的记录。
- 陌生 agent 暴露的 spec/plan 缺陷，以及修订前后关键 diff。

`AGENT_LOG.md` 每条记录必须包含：

- 时间戳和 task 编号。
- 触发的 Superpowers 技能。
- 关键 prompt/context 配置。
- subagent 输出关键片段或 commit hash。
- 人工干预：改了什么、为什么。
- 学到的教训。

## A 类 Harness 实现边界

交付产物必须包含自己编码实现的 harness 内核。可以使用 AI 工具帮助开发，但不能让宿主智能体、现成 agent 框架或高层 agent runner 替代交付产物自身的核心机制。

必须自己实现：

- agent 主循环：组织上下文、调用 LLM、解析动作、分发执行、回灌结果、停机判断。
- 可注入 mock/stub 的 LLM 抽象层。
- 工具/动作分发机制。
- 上下文与记忆机制。
- 治理护栏，包括危险动作识别、拦截和必要的人类确认。
- 客观反馈循环，包括测试、lint、类型检查或自定义校验器结果回灌。
- 声明式配置读取与执行约束。

允许使用：

- LLM 供应商的单次对话补全 API。
- HTTP 客户端、解析库、CLI 参数库、keyring 类库、向量库等底层零件。
- 测试框架、mock 框架、容器构建工具、打包工具。

禁止使用作为核心实现：

- LangChain `AgentExecutor`。
- AutoGen、CrewAI、LlamaIndex agent 等高层 agent 编排框架。
- 宿主编码智能体 SDK 自带的 agent runner。
- 任何已经替你实现主循环、工具治理、反馈闭环和记忆调度的高层框架。

判断标准：移除真实 LLM 后，核心机制仍能由 mock/stub LLM 驱动并用确定性单元测试验证。做不到这一点的“机制”，不计入有效 harness 实现。

## 机制必须是代码

危险动作拦截、反馈信号、记忆读写、工具分发、停机判断都必须落实为确定性的代码机制，不能只写在 prompt 或规则文件里。

不合格示例：

```text
在系统提示词里写：不要执行危险命令。
```

合格示例：

```text
guardrail(action) 检测到删除数据库、删除项目根目录、发布到外部 registry 等危险动作时，返回 blocked，并要求 HITL 审批。
```

测试应能直接构造动作对象并断言拦截结果，不依赖真实 LLM 是否听话。

## 主贡献深度

六个 harness 维度都要有可运行的最低实现：

- 决策封装。
- 工具/动作。
- 上下文与记忆。
- 治理护栏。
- 反馈闭环。
- 配置。

但必须选择一个机制密集维度作为主贡献深入实现。优先考虑：

- 治理：guardrail、sandbox、HITL 状态机、范围围栏。
- 反馈闭环：确定性 sensor、失败分类、多轮自我修正。
- 扩展/工具分发：工具注册、权限分级、多 agent 隔离。
- 记忆/上下文：自建存储、检索、压缩和按需注入。

不要六个维度都浅尝辄止。`SPEC.md` 必须解释选择哪个维度做深、为什么、如何编码实现、如何确定性测试。

## TDD 纪律

TDD 是硬性要求。任何功能或 bugfix 都必须：

1. 先写失败测试。
2. 运行测试并确认失败原因符合预期。
3. 写最少实现使测试通过。
4. 再运行测试确认通过。
5. 必要时重构，并保持测试通过。

禁止：

- 先写实现再补测试。
- 没看到红灯就宣称遵循 TDD。
- 用真实 LLM、真实网络或真实 API key 作为核心单元测试前提。
- 为了让测试过而削弱需求或删除断言。

核心机制测试必须使用 mock/stub LLM，离线、确定、可重复。

必须包含机制演示，至少复现：

- 治理护栏拦截一个危险动作。
- 注入一次失败后，反馈闭环让 agent 收到反馈并改变下一步动作。
- 主贡献维度的一个确定性行为。

机制演示可以是测试用例或可重复运行脚本。

## 评审纪律

每个 task 完成后必须两阶段评审：

1. Spec 合规检查：实现是否满足 `SPEC.md` 和 `PLAN.md` 对该 task 的要求。
2. 代码质量检查：边界、错误处理、测试质量、可维护性、安全性、最小实现原则。

Critical issue 必须修复后才能进入下一 task。

评审时优先报告问题、风险和缺失测试，不要先写笼统总结。若没有发现问题，也要说明剩余风险或未覆盖场景。

## 凭据安全

凡调用付费 LLM 或其它需鉴权 API，必须安全处理凭据：

- 真实 key 绝不硬编码进源码。
- 真实 key 绝不提交进 Git，包括历史。
- 真实 key 绝不写入日志、测试快照、终端 history 或明文配置文件。
- 查看 key 状态时不得回显明文。
- 首次运行必须能引导用户安全录入 key，例如隐藏输入。
- 必须能查看状态、更新和清除 key。

至少实现一种安全存储：

- Windows Credential Manager。
- macOS Keychain。
- Linux Secret Service。
- 密钥管理服务。
- 带主密码的加密文件。

环境变量或 `.env` 可以作为输入来源，但 `.env` 是明文，必须在 `SPEC.md` 和 `README.md` 说明风险，并确保 `.env` 不被提交。

`SPEC.md` 必须包含凭据威胁模型与对策。

## 分发与运行

必须回答：别人如何获取项目并运行起来，且如何安全配置自己的 key。

至少选择一种分发形态：

- 容器镜像：`docker build` + `docker run` 可启动，并说明 registry。
- 原生可执行二进制：说明目标平台、CPU 架构、签名或系统拦截处理。
- 包管理器分发：npm、PyPI、cargo、Homebrew 等，给出安装命令。

`README.md` 必须写清：

- 获取方式。
- 安装命令。
- 运行命令。
- key 在目标机器上的安全配置方式。
- 已知限制：平台、架构、依赖前提。
- 安全边界说明。
- 目录结构。

如果项目包含服务端或 WebUI，最终必须提供截止前可访问的公网 URL，并说明部署架构和 CI/CD。

最终交付必须提供应用可访问的 WebUI 接口。即使 harness 核心是 CLI，也应规划一个最小可用 WebUI 用于演示运行、配置状态、机制演示或日志查看。

## CI 与测试命令

必须提供一键测试命令，例如 `make test` 或等价命令。

必须配置 `.gitlab-ci.yml`，且包含名为 `unit-test` 的 job。

CI 要求：

- 每次 push 自动运行测试。
- 最后一次 CI/CD 执行必须是 pass 状态。
- 如选择容器分发，CI 应构建镜像。
- 如选择二进制分发，鼓励 CI 产出可下载构建产物。

在声明“完成”“通过”“可运行”之前，必须刚刚运行对应验证命令，并阅读完整输出。

## Git 与分支

最终仓库必须是公开 GitHub 仓库；如私有仓，需按课程要求添加助教为协作者。

要求：

- 保留完整 commit 历史和 PR 工作流。
- 拒绝单次 commit 提交全部代码。
- 每个 worktree 对应一个 PR。
- commit message 或 PR 描述中标注由哪个 subagent 完成、人工修改了哪些部分。
- 提交前检查真实凭据、`.env`、配置文件、日志和历史。

当前工作区如果尚未初始化 Git，不要擅自初始化或远程推送，除非用户明确要求。

## 实现原则

- 深度优先，不用代码量堆复杂度。
- 至少 3 个职责清晰的功能模块。
- 最小代码解决问题，不做未要求的功能。
- 不为单次使用创建抽象。
- 不把现成框架薄封装成“自己实现的 harness”。
- 不做无关重构。
- 匹配项目既有风格；项目风格尚未形成时，先在 `SPEC.md` 中确定。
- 对结构化数据使用结构化解析器，不用脆弱字符串拼接。
- 对危险命令、文件写入、外部发布等动作设置明确边界。
- 对长任务使用清晰 task 状态，避免偏离目标。

## Windows 与中文编码

本项目路径和文档包含中文，默认在 Windows PowerShell 环境下工作。

读取中文 Markdown 或源码时：

```powershell
Get-Content -Encoding UTF8 -LiteralPath <path>
```

向 Python、Node、git、rg 等原生命令管道传中文前：

```powershell
$OutputEncoding = [Text.UTF8Encoding]::new($false)
```

写入中文文件必须确保 UTF-8。Windows PowerShell 5.1 中不要依赖 `Set-Content` 默认编码；必要时使用支持 UTF-8 no BOM 的工具或 .NET 写入。编辑后至少用 `Get-Content -Encoding UTF8` 重读关键文件，检查是否乱码、缺行或残留占位符。

## 禁止事项

- 不要在 spec/plan/cold-start validation 完成前写实现代码。
- 不要把 prompt 当作代码机制。
- 不要用真实 LLM 结果证明核心机制正确。
- 不要提交真实凭据或会泄露凭据的日志。
- 不要删除或改写用户未要求修改的内容。
- 不要用单次最终 commit 掩盖过程。
- 不要让 subagent 在没有明确 task、边界和验证步骤时自由发挥。
- 不要在测试未运行或失败时声称完成。
- 不要用“看起来可以”“应该能跑”替代验证。
- 不要让 README、SPEC、PLAN、AGENT_LOG 与实际实现互相矛盾。

## 验收口径

只有同时满足以下条件，才可以称为项目完成：

- `SPEC.md`、`PLAN.md`、`SPEC_PROCESS.md`、`AGENT_LOG.md`、`README.md`、`REFLECTION.md` 均存在并满足课程要求。
- harness 内核由本项目代码实现，非高层 agent 框架代替。
- mock/stub LLM 下的确定性单元测试覆盖核心机制。
- 机制演示可重复运行。
- 一键测试命令通过。
- `.gitlab-ci.yml` 包含 `unit-test`，最后一次 CI/CD pass。
- 凭据安全存储、录入、状态查看、更新、清除流程可用并有文档。
- 至少一种分发方式可用，README 给出从零运行步骤。
- WebUI 可访问并能展示项目核心能力或机制演示。
- 没有真实凭据进入仓库。
- 过程日志能说明 Superpowers 工作流、subagent 使用、人工评审和修正。

本项目的目标不是让 AI 替人完成作业，而是证明人能用工程纪律驾驭 AI：让智能体生成解，让测试、评审、护栏和人的判断负责验证解。
