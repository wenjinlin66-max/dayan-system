# 风险检查单

- [ ] workflow 草稿 / 发布版是否混用
- [ ] approval resume 是否可能恢复到错误 execution
- [ ] dept_id 权限过滤是否覆盖查询与执行
- [ ] event envelope 是否有缺字段风险
- [ ] tool 调用失败后是否有兜底
- [ ] RAG 检索是否可能跨部门泄露
- [ ] SSE 状态是否与 execution 实际状态不一致
