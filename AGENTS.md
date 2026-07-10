# AGENTS.md

补充项目规则（与 CLAUDE.md 一起被 Config 系统加载）。

本文件为可选文件，不存在时不影响运行。

## 编码约定

- 使用 Python 3.11+ 语法，包括 `X | None` 联合类型简写
- 使用 `from __future__ import annotations` 延迟求值
- 遵循 ruff 规则集
- 使用 mypy 严格模式进行类型检查

## 安全约束

- 所有凭据通过 keyring 存储，不写入明文文件
- 危险命令模式在 `governance.py` 中硬编码拦截
- 文件写入限制在 `allowed_dirs` 范围内