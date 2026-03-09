# Workflow 发布状态机

## 1. 版本状态
- `draft`：可编辑，不可正式执行
- `compiled`：已通过编译，生成 execution_dag
- `released`：正式发布，可用于生产执行
- `sandbox`：草稿沙盒测试态
- `archived`：归档，不可新建执行

## 2. 状态流转
```text
draft -> compiled -> released
draft -> sandbox
compiled -> draft
released -> archived
released -> draft(next version)
```

## 3. 发布规则
- 发布动作由 Python 完成
- 发布前必须已有成功编译的 `execution_dag`
- 每个 workflow 同一时刻只能有一个 `current_release_version`
- 新版本发布后，旧版本保留历史但不再是 current release

## 4. 沙盒规则
- sandbox 仅用于测试画布草稿
- sandbox 执行记录与正式执行记录必须可区分
- sandbox 不进入正式业务审计口径

## 5. 执行选择规则
- 默认执行 `released` 版本
- 若明确指定 `mode=sandbox`，则允许执行指定 draft 版本
- 子流程引用默认只允许引用 released 版本

## 6. 失败处理
- 编译失败时保持 draft，不允许进入 released
- 发布失败时不得修改 current release 指针
- 恢复或重试发布必须幂等
