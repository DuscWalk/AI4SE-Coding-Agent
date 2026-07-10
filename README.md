# Coding Agent Harness

从零实现的 Coding Agent Harness 内核。核心理念：**Agent = LLM x Harness** -- LLM 只负责"下一步做什么"这一行任务决策，harness 负责让它稳定工作所需的工具、记忆、治理、反馈和配置。

本项目是南京大学《智能化软件工程训练》期末项目 A 类交付物，使用 Python 3.11+ 分层架构实现，以**反馈闭环**为主贡献维度。

---

## 获取

```bash
git clone <repo-url>
cd agent
```

## 安装

```bash
pip install -e ".[dev]"
```

这将安装 `coding-agent-harness` 包及其开发依赖（pytest、ruff、mypy）。

## 运行

启动 Web 服务（默认端口 8080）：

```bash
coding-agent serve --port 8080
```

打开浏览器访问 `http://localhost:8080` 即可使用 WebUI。

如需查看所有可用命令：

```bash
coding-agent --help
```

## API Key 配置

本项目使用操作系统原生凭据存储（Windows Credential Manager / macOS Keychain / Linux Secret Service），不落地明文文件。

```bash
# 录入 API key（隐藏输入，不回显）
coding-agent credentials set

# 查看状态（只显示是否已配置，不显示明文）
coding-agent credentials status

# 更新 API key（覆盖旧值）
coding-agent credentials set

# 清除 API key
coding-agent credentials clear
```

**环境变量备选方案**：也可以设置环境变量 `CODING_AGENT_API_KEY` 或 `OPENAI_API_KEY`。首次运行时会自动检测。**注意**：`.env` 文件为明文存储，存在泄露风险，不推荐在生产环境使用。如必须使用 `.env`，请确保其已被 `.gitignore` 排除。

**支持的 LLM 供应商**：任何兼容 OpenAI API 协议的服务均可使用（OpenAI、Claude API、DeepSeek 等），通过 `OPENAI_BASE_URL` 环境变量或 `config.yaml` 中的 `model` 配置指定。

## 测试

一键运行所有测试：

```bash
pytest tests/ -v
```

运行机制演示（核心行为验证）：

```bash
pytest tests/demonstrations/ -v
```

测试覆盖：
- 核心机制单元测试（mock LLM，确定性、离线、可重复）
- 治理护栏拦截演示
- 反馈闭环：失败注入后自我修正演示
- 反馈管线：sensor -> 分类 -> 策略 -> 回灌全链路演示

## 分发

### Docker

```bash
docker build -t coding-agent .
docker run -p 8080:8080 -v ~/.coding-agent:/root/.coding-agent coding-agent
```

### PyPI（开发中）

```bash
pip install coding-agent-harness
coding-agent serve --port 8080
```

## 部署

项目已部署至阿里云 ECS，可通过以下公网地址访问：

**http://120.26.110.68:8081**

### 部署架构

| 组件 | 说明 |
|------|------|
| **服务器** | 阿里云 ECS（Linux x86_64） |
| **进程管理** | systemd（`/etc/systemd/system/coding-agent.service`） |
| **Python** | 3.11（venv 虚拟环境） |
| **路径** | `/opt/coding-agent/` |
| **凭据后端** | Linux Secret Service（keyrings.alt） |
| **安全组** | 开放 8081 端口 |

### CI/CD

CI 配置位于 `.gitlab-ci.yml`，包含 `unit-test` job：每次 push 自动运行 `pytest tests/ -v --tb=short`。Docker 镜像构建与部署通过手动触发。

## 已知限制

| 限制 | 说明 |
|------|------|
| **Python 版本** | 需要 Python 3.11 或更高版本 |
| **操作系统** | 开发/测试：Windows 11；部署：Docker（Linux x86_64）。凭据存储在 Windows 上使用 Credential Manager，macOS 使用 Keychain，Linux 使用 Secret Service |
| **向量存储** | 记忆模块使用 InMemoryVectorStore（SHA-256 哈希嵌入 + 余弦相似度检索），无外部依赖 |
| **真实 LLM 依赖** | 核心机制使用 mock LLM 测试，不依赖真实 LLM。实际运行需要配置有效的 LLM API key 和网络连接 |
| **Web 前端** | 使用原生 HTML/CSS/JS，无前端框架依赖，轻量但交互能力有限 |
| **subprocess 超时** | 工具执行的默认超时为 120 秒，可通过配置调整 |

## 安全边界

### 治理护栏

工具分为三个权限级别：

| 级别 | 行为 | 示例工具 |
|------|------|----------|
| **SAFE** | 直接放行 | `read_file`, `list_dir`, `search_files`, `grep`, `run_test`, `git_status`, `git_diff` |
| **RISKY** | 需用户确认 | `write_file`, `git_commit` |
| **DANGEROUS** | 需 HITL 审批 | `run_shell` |

**硬拦截**（不可绕过，直接 BLOCKED）：

- `rm -rf /`、`del /f /s C:\` 等破坏性删除
- `DROP TABLE`、`DELETE FROM` 等数据库破坏操作
- `git push --force main` 等强制推送主分支
- `chmod 777 /`、`format C:` 等系统级破坏
- `pip publish`、`docker push`、`npm publish` 等外部发布

**注意**：护栏是代码机制（`governance.py`），不是 prompt 提示词。单元测试可直接构造 Action 对象并断言 PermissionResult。

### 文件访问控制

- 通过 `allowed_dirs` 配置限定 agent 的工作目录范围
- 默认仅允许当前项目目录，防止访问系统敏感路径

### 凭据安全

- API key 存储在操作系统原生凭据管理器（Windows Credential Manager / macOS Keychain / Linux Secret Service），加密保护
- API key **绝不**进入 Git 历史、日志文件、终端输出或测试快照
- 日志系统自动脱敏，替换 key 为 `****`
- `.env` 文件已被 `.gitignore` 排除

### 步数与超时限制

- 默认最大步数 50 步，防止无限循环
- 工具执行超时默认 120 秒
- HITL 审批超时默认 5 分钟，超时视为拒绝

## 架构概览

```
Presentation  (FastAPI + WebSocket + 静态前端)
     │
Application   (AgentLoop / SessionManager / ActionParser)
     │
Domain        (ToolManager / Governance / FeedbackPipeline / Memory / Config)
     │
Infrastructure (LLMProvider / CredentialStore / VectorStore / FileSystem / SubprocessManager)
```

详细设计见 `SPEC.md`，实现计划见 `PLAN.md`。

## 目录结构

```
.
├── .github/workflows/ci.yml          # GitHub Actions CI 配置（unit-test job）
├── .gitignore
├── .gitlab-ci.yml                  # CI 配置（unit-test job）
├── AGENTS.md                       # 补充项目规则
├── CLAUDE.md                       # 项目 agent 操作章程
├── Dockerfile                      # Docker 镜像构建文件
├── Makefile                        # 一键测试与构建命令
├── PLAN.md                         # 实现计划
├── README.md
├── REFLECTION.md                   # 个人反思报告
├── SPEC.md                         # 设计文档
├── SPEC_PROCESS.md                 # 规约生成过程记录
├── pyproject.toml                  # 项目元数据与依赖
├── coding_agent/                   # 主包
│   ├── __init__.py
│   ├── main.py                     # CLI 入口（credentials, serve 等命令）
│   ├── application/                # 应用层
│   │   ├── __init__.py
│   │   ├── action_parser.py        # LLM 输出 -> 结构化 Action
│   │   ├── agent_loop.py           # 主循环编排
│   │   └── session_manager.py      # 会话生命周期管理
│   ├── domain/                     # 领域层
│   │   ├── __init__.py
│   │   ├── config.py               # 声明式配置加载
│   │   ├── governance.py           # 治理护栏（三级权限 + HITL）
│   │   ├── memory.py               # 上下文与记忆（向量检索 + 压缩）
│   │   ├── models.py               # 核心数据模型（Pydantic）
│   │   ├── tool_manager.py         # 工具注册与分发
│   │   ├── feedback/               # 反馈闭环（主贡献维度）
│   │   │   ├── __init__.py
│   │   │   ├── classifier.py       # 失败分类器
│   │   │   ├── engine.py           # 修正策略引擎
│   │   │   ├── pipeline.py         # 反馈管线编排
│   │   │   └── sensors.py          # Sensor 管线（语法/类型/lint/测试）
│   │   └── tools/                  # 工具实现
│   │       ├── __init__.py
│   │       ├── file_tools.py       # 文件读写工具
│   │       ├── git_tools.py        # Git 操作工具
│   │       ├── search_tools.py     # 文件搜索与内容搜索
│   │       ├── shell_tool.py       # Shell 命令执行
│   │       └── test_tool.py        # 测试运行工具
│   ├── infrastructure/             # 基础设施层
│   │   ├── __init__.py
│   │   ├── credential_store.py     # 凭据安全存储（keyring）
│   │   ├── file_system.py          # 文件系统抽象
│   │   ├── llm_provider.py         # LLM 抽象接口 + mock 实现
│   │   ├── real_llm.py             # 真实 LLM（OpenAI 兼容协议）
│   │   ├── subprocess_manager.py   # 子进程管理
│   │   └── vector_store.py         # 向量存储（ChromaDB）
│   └── presentation/               # 表示层
│       ├── __init__.py
│       ├── app.py                  # FastAPI 应用
│       ├── routes.py               # REST API 路由
│       ├── websocket.py            # WebSocket 实时推送
│       └── static/                 # 前端静态资源
│           ├── DESIGN.md           # Open Design 设计系统文档
│           ├── app.js              # 前端交互逻辑
│           ├── index.html          # WebUI 页面
│           └── style.css           # 样式
├── docs/                           # 课程文档
│   ├── AI4SE_Final_Project_A_Coding_Agent_Harness.md
│   ├── AI4SE_Final_Project_通用要求.md
│   ├── Agent 的一生 · 一段伪代码看懂全过程.html
│   ├── AgenticEngineering-with-notes.pptx
│   ├── pecehe-with-notes.pptx
│   └── 如何成为智能化软件工程师.pdf
└── tests/                          # 测试
    ├── __init__.py
    ├── conftest.py                 # 共享 fixtures（mock LLM 等）
    ├── application/                # 应用层测试
    │   ├── test_action_parser.py
    │   ├── test_agent_loop.py
    │   └── test_session_manager.py
    ├── demonstrations/             # 机制演示
    │   ├── test_demo_feedback.py   # 反馈闭环演示
    │   ├── test_demo_governance.py # 治理护栏演示
    │   └── test_demo_pipeline.py   # 完整管线演示
    ├── domain/                     # 领域层测试
    │   ├── test_config.py
    │   ├── test_governance.py
    │   ├── test_memory.py
    │   ├── test_models.py
    │   ├── test_tool_manager.py
    │   ├── test_feedback/
    │   │   ├── test_classifier.py
    │   │   ├── test_engine.py
    │   │   ├── test_pipeline.py
    │   │   └── test_sensors.py
    │   └── test_tools/
    │       ├── test_file_tools.py
    │       └── test_shell_tool.py
    ├── infrastructure/             # 基础设施层测试
    │   ├── test_credential_store.py
    │   ├── test_file_system.py
    │   ├── test_llm_provider.py
    │   ├── test_subprocess_manager.py
    │   └── test_vector_store.py
    └── presentation/               # 表示层测试
        └── test_app.py
```

## 文档索引

- `SPEC.md` -- 设计文档：问题陈述、用户故事、功能规约、架构、数据模型
- `PLAN.md` -- 实现计划：任务分解、依赖关系、验证步骤
- `SPEC_PROCESS.md` -- 规约生成过程：brainstorming 记录、冷启动验证
- `AGENT_LOG.md` -- Agent 协作日志：Superpowers 工作流执行记录
- `REFLECTION.md` -- 个人反思报告（1500-2500 字）
- `CLAUDE.md` -- 项目级 agent 操作章程

## 许可证

本项目为课程作业，仅供学习使用。