---
name: ai-hotspot-to-feishu
description: 用于抓取网上 AI 热点资讯并自动同步到飞书文档。当用户提出“抓取AI热点”“同步AI资讯到飞书文档”“做AI日报并推送飞书”时触发。
---

# AI 热点到飞书

## 概述

本 skill 提供一条可自动化执行的链路：抓取多来源热点 -> 关键词过滤 -> 去重排序 -> 生成中文摘要 -> 追加到飞书文档。

## 触发条件

- “抓取网上 AI 热点并发到飞书文档”
- “帮我做一份 AI 日报并同步飞书”
- “定时同步 AI 新闻到飞书”

## 工作流

### 1. 读取配置
- 读取环境变量：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`
- 读取目标文档：`FEISHU_DOC_URL` 或 `FEISHU_DOC_TOKEN`
- 可选读取：`HOTSPOT_LIMIT`、`HOTSPOT_HOURS`、`HOTSPOT_KEYWORDS`

### 2. 抓取热点
- RSS：OpenAI News、Anthropic News、Google News(AI)
- API：Hacker News（Algolia）
- 保留时间窗内内容，并做关键词过滤

### 3. 数据清洗
- 按链接去重
- 按发布时间与来源热度排序
- 为每条生成详细中文摘要与完整总结（优先使用原文正文）

### 4. 写入飞书文档
- 支持 `docx` 链接和 `wiki` 链接
- 解析 wiki 节点并转换到 docx 文档 token
- 以“日期标题 + 条目列表”的形式追加内容
- 可通过计划任务每天 12:00 自动执行

### 5. 输出结果
- 返回抓取条数、写入状态、失败原因（如有）

## 执行方式

```bash
python .opencode/skills/ai-hotspot-to-feishu/scripts/sync_ai_hotspot_to_feishu.py
```

可选参数：

```bash
python .opencode/skills/ai-hotspot-to-feishu/scripts/sync_ai_hotspot_to_feishu.py --limit 15 --hours 48
```

## 输出规范

- 标题格式：`AI 热点简报 YYYY-MM-DD HH:mm`
- 每条包含：标题、来源、发布时间、中文摘要、原文链接
- 默认按“最新优先”输出

## 参考文档

- 使用说明：`references/usage_guide.md`
- 环境变量模板：`references/env_template.md`
- 飞书 API 说明：`references/feishu_api_notes.md`
