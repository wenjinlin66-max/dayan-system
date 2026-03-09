---
name: teacher-jobs-to-feishu
description: 用于抓取广东教师招聘官网公告并将符合“广州/惠州/深圳/东莞 + 初中/高中 + 生物教师”条件的岗位同步到飞书多维表格。当用户提出“抓取教师编岗位”“同步生物教师岗位到飞书多维表格”“做教师岗位监控并推送飞书”时触发。
---

# 教师岗位到飞书多维表格

## 概述

本 skill 提供一条可自动执行链路：采集官方公告 -> 关键词筛选 -> 学段/学科/地区匹配 -> 去重 -> 写入飞书多维表格。

## 工作流

### 1. 配置环境变量

- 必填：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`
- 二选一：
  - `FEISHU_BITABLE_URL`（推荐）
  - `FEISHU_BITABLE_APP_TOKEN` + `FEISHU_BITABLE_TABLE_ID`
- 采集源配置：`JOB_SOURCE_CONFIG`（默认读取 `references/sources_template.json`）

### 2. 抓取与筛选

- 仅采集配置中的官方公告页
- 通过关键词匹配岗位：
  - 地区：广州、惠州、深圳、东莞
  - 学段：初中或高中
  - 学科：生物
- 支持可选区县白名单（如天河区、南山区等）
- 默认过滤时间窗：30 天（可通过环境变量调整）
- 支持进入公告正文二次匹配（不只依赖标题）

### 2.1 附件表格识别

- 自动发现公告中的 `.xlsx/.xls/.csv` 附件
- 自动下载到本地并读取岗位表行信息
- 将命中的岗位行摘要作为“匹配证据”写入飞书

### 3. 去重

- 本地去重：`scripts/data/seen_jobs.json`
- 对同一公告链接只写入一次

### 4. 写入飞书多维表格

- 自动识别可用数据表（若未指定 `FEISHU_BITABLE_TABLE_ID`，默认取第一个表）
- 优先写入字段：
  - `岗位标题`、`地区`、`学段`、`学科`、`公告链接`、`来源网站`、`发布时间`、`抓取时间`、`匹配说明`
- 若目标表字段不一致，会自动降级写入一个可用文本字段，避免全量失败

## 执行方式

```bash
python .opencode/skills/teacher-jobs-to-feishu/scripts/sync_teacher_jobs_to_feishu.py
```

可选参数：

```bash
python .opencode/skills/teacher-jobs-to-feishu/scripts/sync_teacher_jobs_to_feishu.py --max-items 30 --lookback-days 45
```

## 参考

- 环境变量模板：`references/env_template.md`
- 采集源模板：`references/sources_template.json`
- 使用说明：`references/usage_guide.md`
