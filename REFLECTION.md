# REFLECTION.md · 个人反思报告

## 一、项目概述与我的角色

本项目是南京大学 AI4SE 课程期末项目 A 类——从零实现一个 Coding Agent Harness。核心公式是 `Agent = LLM × Harness`，即 LLM 只负责基于上下文做下一步决策，而 harness 负责让这个决策过程稳定、安全、可验证地运行。

我承担的角色是**项目架构师和工程把关者**。在 Superpowers 工作流中，我的职责不是手写每一行代码，而是：
1. 通过 brainstorming 将模糊需求转化为可审查的设计规约
2. 通过 writing-plans 将设计拆分为 2-5 分钟粒度的可执行任务
3. 通过冷启动验证确保 plan 对陌生 agent 可执行
4. 通过 subagent-driven development 调度独立 agent 执行每个 task
5. 在每个 task 完成后进行两阶段评审（spec 合规 + 代码质量）

这种工作方式与传统的"一人一键盘"开发模式截然不同，它要求我在"做什么"和"做对了吗"两个层面投入更多精力，而把"怎么做"的细节委托给 subagent。

## 二、Superpowers 工作流的真实体验

### 2.1 brainstorming 阶段：从模糊到清晰

brainstorming 阶段最让我意外的是**设计决策的分量**。8 轮问答涵盖了主贡献维度、技术栈、LLM 抽象、反馈深度、工具规模、记忆方案、治理策略和架构模式。每个决策都会影响后续所有 task 的形态。

选择"反馈闭环"作为主贡献维度是一个关键决策。它意味着整个 harness 的设计围绕反馈管线展开：Sensor → Classifier → Engine → Pipeline。这个决策影响了 6 个独立 task（10-14、24），约占全部 task 的四分之一。

推翻 AI 建议的部分也值得反思。AI 建议使用 React 前端，但课程要求轻量，原生 HTML/CSS/JS 更简单。AI 建议引入 Redis，但单机内存即可满足需求。这些决策体现了"YAGNI"原则——不做未要求的功能，不为单次使用创建抽象。

### 2.2 writing-plans 阶段：从设计到可执行任务

将 SPEC.md 转化为 26 个 task 的过程中，最大的挑战是**粒度控制**。每个 task 必须在 2-5 分钟内完成，且必须包含完整的代码和验证步骤。这意味着不能写"实现 XX 功能"这样的模糊描述，而必须写出具体的文件路径、测试代码和预期输出。

初始 PLAN.md 的 Task 1 包含了 5 个步骤（创建目录、编写 pyproject.toml、创建 __init__.py、pip install、验证），跨度太大。冷启动验证后拆分为 Task 1a（项目骨架）和 Task 1b（安装验证），每个 task 都有明确的验证命令。

### 2.3 冷启动验证：最有价值的工程实践

冷启动验证是本次项目最让我震撼的环节。我配置了一个 Sonnet general-purpose agent，它没有本项目的任何对话上下文，只拿到 SPEC.md 和 PLAN.md 两个文件路径。要求它独立完成 Task 1 和 Task 2。

结果令人信服：agent 成功完成了两个 task，包括 TDD 红-绿-重构和两次 git commit。但它也暴露了一个关键 bug——`build-backend = "setuptools.backends._legacy:_Backend"` 是无效值。agent 在无人干预的情况下自行修正为 `setuptools.build_meta`。

这个发现让我意识到：**人类 review 容易忽略的事实性错误，陌生 agent 反而能发现**。因为 agent 会逐字逐句地执行 plan 中的命令，任何无效值都会在执行时暴露。而人类 review 时可能只是扫一眼，不会真正运行每个命令。

这证明了 CLAUDE.md 中"冷启动验证是硬性门禁"的合理性。如果直接用原始 PLAN.md 进入实现，中间会遇到可避免的阻碍。

### 2.4 subagent-driven development：调度与管理

26 个 task 由约 20 个独立的 Sonnet general-purpose agent 执行。每个 agent 都是全新的上下文，只拿到 task 描述和必要的文件路径。这种模式的优势明显：

- **上下文隔离**：每个 agent 不会受前一个 task 的对话历史影响，减少了"幻觉"的累积
- **并行执行**：独立的 task 可以同时 dispatch，如 Task 8（治理）和 Task 9（记忆）可以并行
- **可复现性**：每个 task 的结果是独立的 commit，可以单独 review 和 revert

但也有一些代价：
- **接口不一致**：AgentLoop 的多个接口与 PLAN.md 中的签名不匹配，因为不同 agent 各自实现时可能采用不同的参数顺序或类型
- **上下文传递成本**：每个 agent 需要完整的 task 描述，plan 中的任何模糊之处都会导致 agent 自行发挥

## 三、技术深入：反馈闭环的主贡献实现

反馈闭环是本次项目的主贡献维度，也是机制最密集的部分。

### 3.1 设计思路

反馈管线按速度排序：语法检查 → 类型检查 → lint → 测试。这个顺序实现了"快速失败"——语法错误时无需等待测试结果，节省等待时间。

4 个 Sensor 各有明确的职责：
- **SyntaxSensor**：使用 `compile()` 检查 Python 语法
- **TypeCheckSensor**：使用 `mypy` 检查类型
- **LintSensor**：使用 `ruff` 检查代码风格
- **TestSensor**：运行 `pytest` 并解析结果

### 3.2 失败分类与修正策略

FailureClassifier 按 category（syntax/type/test/lint/import/timeout/unknown）和 file_path 聚合失败。聚合后的结果传递给 CorrectionEngine。

CorrectionEngine 采用三级渐进策略：
1. **RETRY**：将失败信息注入 LLM 上下文，让 agent 重新尝试
2. **ROLLBACK**：撤销最近的文件变更，回到已知良好状态
3. **ASK_USER**：当自动修正失败超过阈值时，升级为人工介入

这个渐进式升级策略避免了死循环——超过最大重试次数自动升级，而不是无限重试。

### 3.3 确定性测试

所有反馈管线的测试都使用 mock LLM。例如，机制演示 2（test_demo_feedback.py）注入一个语法错误文件，然后验证 Sensor 检测到错误、Classifier 分类为 SYNTAX_ERROR、Engine 返回 RETRY 策略。整个过程不需要真实 LLM，完全确定性和可重复。

## 四、治理与安全：从 prompt 到代码

CLAUDE.md 中有一条关键原则：**机制必须是代码，不能只写在 prompt 里**。

治理护栏的实现体现了这一点：
- `BLOCKED_PATTERNS` 包含 `rm -rf /`、`DROP TABLE`、`git push --force main`、`chmod 777 /`、`format C:` 等危险命令模式
- 硬拦截模式不可通过 HITL 绕过——即使人类确认，这些命令也永远不会执行
- 三级权限（SAFE/RISKY/DANGEROUS）决定了哪些操作需要人类确认

测试可以直接构造动作对象并断言拦截结果，不依赖真实 LLM 是否听话。这比"在 prompt 里写不要执行危险命令"可靠得多。

## 五、挑战与应对

### 5.1 平台差异

Windows PowerShell 与 Linux bash 的差异是持续挑战。`mkdir -p` 不可用，单引号在 cmd.exe 中不被识别，subprocess timeout 的错误消息格式不同。冷启动验证暴露了这些问题，PLAN.md 修订后所有命令都改为 PowerShell 语法。

### 5.2 接口一致性问题

随着 task 数量增加，不同 agent 实现的接口之间出现了不一致。例如 AgentLoop 依赖的 Governance 接口、SessionManager 的 complete() 签名等在 PLAN.md 中与实际实现有差异。后续 agent 在遇到这些不一致时自行修正了接口，但这也暴露了 PLAN.md 在接口定义上需要更精确。

### 5.3 测试策略的权衡

109 个测试全部使用 mock LLM，这是正确的选择——它确保了测试的确定性、可重复性和离线运行能力。但这也意味着没有测试覆盖真实 LLM 的行为。在生产环境中，真实 LLM 的输出格式可能与 mock 不同，这是一个已知风险。

## 六、收获与反思

### 6.1 工程师的角色转变

这次项目让我深刻体会到**工程师在 AI 时代的角色转变**。传统开发中，工程师负责"做什么"和"怎么做"。在 agentic engineering 中，工程师负责"做什么"和"做对了吗"，而"怎么做"由 AI 完成。

这不是工程师的退场，而是责任的升级。工程师需要：
- 更精确地定义规约和验收标准
- 更严格地执行测试和评审纪律
- 更深入地理解安全边界和失败模式
- 更系统地管理 AI 协作过程

### 6.2 规约的质量决定产出的质量

冷启动验证最深刻的教训是：**规约的质量直接决定 AI 产出的质量**。PLAN.md 中的 `build-backend` 错误、缺少平台说明、task 粒度不均等问题，都会在执行时暴露并导致额外的工作。

好的规约不是"写得多"，而是"写得对"——每个命令可以执行，每个接口签名准确，每个验证步骤有预期输出。

### 6.3 TDD 在 agentic 开发中的价值

TDD 在 agentic 开发中比传统开发更有价值。因为 AI 生成的代码可能包含看不见的错误，而测试是唯一客观的验证手段。先写测试再写实现，确保了：
1. 测试不会因为"实现已经通过"而被省略
2. 每个功能都有对应的失败测试作为"红灯"证据
3. Mock LLM 的使用被强制纳入测试设计

### 6.4 如果重来一次

如果有机会重新做这个项目，我会做以下改进：
1. **在 PLAN.md 中定义接口契约**：为每个模块的公开接口定义精确的类型签名，减少 agent 间的不一致
2. **更早引入集成测试**：在 Phase 2 就开始写跨模块的集成测试，而不是等到 Phase 5
3. **增加冷启动验证的覆盖范围**：不只是验证 Task 1-2，而是验证每个 phase 的入口 task
4. **使用 worktree 隔离**：为每个 phase 创建独立的 git worktree，进一步减少上下文污染

## 七、结论

本次项目通过 Superpowers 工作流，完成了从零到交付的完整 Coding Agent Harness 实现。27 个 commit、109 个测试、3 个机制演示、完整的 WebUI 和 Docker 分发——所有这些都通过 subagent-driven development 完成，由 mock LLM 确定性地验证。

最重要的收获是：**工程纪律是驾驭 AI 的前提**。brainstorming 的设计决策、writing-plans 的精确分解、TDD 的测试先行、冷启动验证的质量门禁、两阶段评审的合规检查——这些纪律不是束缚，而是确保 AI 产出可验证、可信任的保障。

Agent = LLM × Harness 这个公式不仅适用于我们要构建的系统，也适用于我们构建它的过程。LLM 是强大的推理引擎，但只有通过 harness 式的工程纪律——规约、计划、测试、评审、护栏、反馈——才能让 AI 的能力转化为可靠的软件。

---

*字数统计：约 2440 字*