# Maxwell 自动化实现检查单（先实现，不执行）

## A. 环境与配置

- [ ] 已确认 AEDT 根路径
- [ ] 已确认版本（2023 R1）
- [ ] 已确认 license server（1055@LAPTOP-DGVONA4D）
- [ ] 已写入 `maxwell_env_template.env`
- [ ] 已设置 `MAXWELL_EXECUTION_MODE=implement_only`

## B. 工具契约

- [ ] 已定义 `health_check`
- [ ] 已定义 `open_or_create_project`
- [ ] 已定义 `set_design_variables`
- [ ] 已定义 `run_setup`
- [ ] 已定义 `export_results`
- [ ] 所有工具响应使用统一 envelope（ok/code/message/data）

## C. 错误处理

- [ ] 已定义标准错误码
- [ ] 能区分路径错误/许可证错误/版本错误
- [ ] `run_setup` 在 implement_only 模式下会返回 `EXECUTION_DISABLED`

## D. 输出约定

- [ ] 输出目录固定到 `results/maxwell-mcp`
- [ ] 导出文件命名规则已固定
- [ ] 失败日志包含可定位信息（路径/配置/步骤）

## E. 进入执行前还需确认

- [ ] `ansysedt.exe` 真实路径可用
- [ ] gRPC 模式是否可用（或需要 COM fallback）
- [ ] 目标 `.aedt` 工程路径和设计名
- [ ] 首批参数集与 setup 名称
