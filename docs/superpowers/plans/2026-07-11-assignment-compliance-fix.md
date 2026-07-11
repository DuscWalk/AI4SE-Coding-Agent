# Assignment Compliance Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复真实启动装配和静态质量门禁，并逐条验证课程作业要求。

**Architecture:** 保持现有分层架构不变，在组合根 `coding_agent/main.py` 创建基础设施实例并注入工具注册函数。类型修复只补全边界契约和消除冲突，不引入新抽象。

**Tech Stack:** Python 3.11+、pytest、ruff、mypy、setuptools、Docker。

---

### Task 1: 真实装配回归保护

**Files:**
- Create: `tests/test_main.py`
- Modify: `coding_agent/main.py`

- [ ] 写 `_create_agent_loop()` 构造测试并确认因缺少 `fs` 失败。
- [ ] 创建 `FileSystemManager` 与 `SubprocessManager` 并注入注册函数。
- [ ] 运行 `pytest tests/test_main.py -v`，预期通过。

### Task 2: ruff 与 strict typing

**Files:**
- Modify: `coding_agent/**/*.py`
- Modify: `pyproject.toml`
- Modify: `Makefile`

- [ ] 运行 ruff 和 strict mypy，保留完整错误清单。
- [ ] 清理未使用导入并补齐类型边界。
- [ ] 修复 `LLMResponse`、`ActionResult`、`MemoryEntry` 等真实类型冲突。
- [ ] 运行 ruff 与 strict mypy，预期零错误。

### Task 3: 全量验证与文档对照

**Files:**
- Modify: `README.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `.gitlab-ci.yml`

- [ ] 运行全部测试与机制演示。
- [ ] 构建 Python 分发包与 Docker 镜像。
- [ ] 按课程通用要求和 A 题要求逐条检查交付物。
- [ ] 修正文档和 CI 中与最终质量门禁不一致的内容。
