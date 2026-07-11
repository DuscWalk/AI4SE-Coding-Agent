# 作业合规修复设计

## 目标

以最小改动修复当前项目的真实启动入口与工程质量门禁，使项目能够通过课程文档要求的功能验证、确定性测试、ruff 检查和 mypy strict 类型检查。

## 范围

- 修复 `_create_agent_loop()` 遗漏基础设施依赖注入的问题。
- 增加真实装配回归测试，覆盖工具注册与 HITL 配置。
- 为现有代码补齐必要类型注解并修复真实类型冲突。
- 清理 ruff 报告的未使用导入。
- 更新质量检查配置与 README 中失实或过期的交付说明。
- 严格对照课程通用要求和 A 题要求重新验收。

## 非目标

- 不新增功能模块。
- 不重构现有架构。
- 不改变治理、反馈、记忆或工具机制的既有行为。
- 不创建提交、不推送远端、不修改线上服务器。

## 验收标准

1. `_create_agent_loop()` 可成功构造，并注册全部预期工具。
2. `pytest tests/ -v --tb=short` 全部通过。
3. `ruff check coding_agent/ tests/` 通过。
4. `mypy coding_agent/ --strict --ignore-missing-imports` 通过。
5. Python 包构建成功；有 Docker 环境时 Docker 镜像构建成功。
6. README、CI 配置和课程交付清单不存在与代码明显矛盾的描述。
