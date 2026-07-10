# REFLECTION.md · 个人反思报告

## 一、项目概述与我的角色

本项目是南京大学 AI4SE 课程期末项目 A 类——从零实现一个 Coding Agent Harness。核心公式是 `Agent = LLM × Harness`，LLM 只负责基于上下文做下一步决策，harness 负责让这个决策过程稳定、安全、可验证地运行。

我的角色是**项目架构师和工程把关者**。在 Superpowers 工作流中，我的职责不是手写每一行代码，而是通过 brainstorming 将模糊需求转化为可审查的设计规约，通过 writing-plans 将设计拆分为可执行任务，通过冷启动验证确保 plan 对陌生 agent 可执行，通过 subagent-driven development 调度独立 agent 执行每个 task，并在每个 task 完成后进行两阶段评审。

## 二、Superpowers 工作流的真实体验

brainstorming 阶段最让我意外的是设计决策的分量。8 轮问答涵盖了主贡献维度、技术栈、LLM 抽象、反馈深度等关键决策。选择"反馈闭环"作为主贡献维度影响了 6 个独立 task。推翻 AI 的 React 建议和 Redis 建议体现了 YAGNI 原则——不做未要求的功能，不为单次使用创建抽象。

writing-plans 阶段最大的挑战是粒度控制。初始 PLAN.md 的 Task 1 包含 5 个步骤，跨度太大。冷启动验证后拆分为 Task 1a 和 Task 1b，每个 task 都有明确的验证命令。

冷启动验证是本次项目最有价值的工程实践。我用一个 Sonnet general-purpose agent（与主开发 Opus 不同类型），仅凭 SPEC.md + PLAN.md 两个文件，要求它独立完成 Task 1 和 Task 2。agent 成功完成了两个 task，但也暴露了关键 bug——`build-backend` 值无效。agent 在无人干预下自行修正。这让我意识到：**人类 review 容易忽略的事实性错误，陌生 agent 反而能发现**。如果直接用原始 PLAN.md 进入实现，中间会遇到可避免的阻碍。

subagent-driven development 模式的优势明显：上下文隔离减少了幻觉累积，独立 task 可并行执行，每个 task 有独立 commit 可单独 review。但代价是接口不一致——不同 agent 可能采用不同的参数顺序或类型，需要后续修正。

## 三、技术深入：反馈闭环与治理

反馈闭环是主贡献维度，按速度排序（语法→类型→lint→测试）实现快速失败。四个 Sensor 各有明确职责，FailureClassifier 按类别和文件聚合失败，CorrectionEngine 采用 RETRY→ROLLBACK→ASK_USER 三级渐进策略，避免死循环。

治理护栏体现了"机制必须是代码"的原则。BLOCKED_PATTERNS 包含 `rm -rf /`、`DROP TABLE` 等危险命令模式，硬拦截不可通过 HITL 绕过。测试可直接构造动作对象并断言拦截结果，不依赖真实 LLM 是否听话——这比"在 prompt 里写不要执行危险命令"可靠得多。

所有核心机制测试都使用 mock LLM，完全确定性和可重复。109 个测试全部通过，无需真实 API key。

## 四、挑战与应对

Windows PowerShell 与 Linux bash 的差异是持续挑战。`mkdir -p` 不可用，keyring 在 Linux 上需要 keyrings.alt 后端。冷启动验证暴露了平台差异问题，PLAN.md 修订后所有命令都改为 PowerShell 语法。

随着 task 数量增加，不同 agent 实现的接口之间出现了不一致，暴露了 PLAN.md 在接口定义上需要更精确。109 个测试全部使用 mock LLM 确保了确定性，但缺少真实 LLM 行为覆盖是一个已知风险。

## 五、收获与反思

**工程师的角色转变**：传统开发中工程师负责"做什么"和"怎么做"。在 agentic engineering 中，工程师负责"做什么"和"做对了吗"，而"怎么做"由 AI 完成。这是责任的升级而非退场。

**规约质量决定产出质量**：PLAN.md 中的 `build-backend` 错误、缺少平台说明、task 粒度不均等问题，都会在执行时暴露。好的规约不是"写得多"，而是"写得对"——每个命令可以执行，每个接口签名准确。

**TDD 在 agentic 开发中的价值**：比传统开发更有价值。AI 生成的代码可能包含看不见的错误，测试是唯一客观的验证手段。先写测试再写实现，确保了测试不会因为"实现已经通过"而被省略。

**如果重来一次**：我会在 PLAN.md 中定义接口契约，更早引入集成测试，增加冷启动验证的覆盖范围，并使用 worktree 隔离。

## 六、补充反思

**Superpowers 技能评估**：`brainstorming`、`subagent-driven-development`、`test-driven-development` 发挥了最大作用。`using-git-worktrees` 和 `requesting-code-review` 形式大于实质——前者因 task 间线性依赖多而增量收益不大，后者作为独立技能增加了流程摩擦。

**最有效的 prompt 策略**：给 subagent 提供完整的 task 上下文——具体文件路径、完整代码示例、精确的验证命令和预期输出。陌生 agent 会在你未明文写下的每个假设处受阻。好的 prompt 不是"写得聪明"，而是"写得完整"。

**凭据与分发**：凭据安全让我意识到"安全"必须从设计阶段就做决策。SPEC.md 的凭据威胁模型表格迫使我在写代码之前就想清楚"key 可能从哪里泄露"。分发（Docker + 公网部署）迫使我想清楚了环境一致性问题——Windows 开发与 Linux 部署的差异两次暴露，每次都是可避免的阻塞。

**对 Superpowers 方法论的批判**：Superpowers 假设工程纪律可以"嵌入"到 AI 协作流程中，这个假设基本成立。但其局限在于：(1) subagent 经常因接口不一致或 plan 模糊产生偏差，评审仍需要人工判断力；(2) plan 不可能事先写清楚所有细节，接口不一致等"未知的未知"很难在 plan 阶段预见；(3) 流程纪律不能替代领域判断——Superpowers 不会告诉你"反馈管线应该按速度排序"。总的来说，Superpowers 是一套有价值的"工程纪律外骨骼"，但它不能替代工程判断力。

## 七、结论

本次项目通过 Superpowers 工作流完成了从零到交付的完整 Coding Agent Harness 实现。41 个 commit、109 个测试、3 个机制演示、完整的 WebUI 和 Docker 分发。

最重要的收获是：**工程纪律是驾驭 AI 的前提**。brainstorming 的设计决策、writing-plans 的精确分解、TDD 的测试先行、冷启动验证的质量门禁——这些纪律不是束缚，而是确保 AI 产出可验证、可信任的保障。Agent = LLM × Harness 这个公式不仅适用于我们要构建的系统，也适用于我们构建它的过程。

---

*字数统计：约 2300 字*
*本文由学生本人撰写，AI 辅助进行了结构润色和排版优化。*