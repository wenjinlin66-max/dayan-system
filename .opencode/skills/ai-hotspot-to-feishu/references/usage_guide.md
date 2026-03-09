# 使用说明

## 1. 准备

1. 在飞书开放平台创建企业自建应用
2. 获取 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`
3. 给应用开通云文档读写权限
4. 确保目标文档对应用可编辑

## 2. 配置

按 `env_template.md` 设置环境变量。

## 3. 执行

```bash
python .opencode/skills/ai-hotspot-to-feishu/scripts/sync_ai_hotspot_to_feishu.py
```

指定参数：

```bash
python .opencode/skills/ai-hotspot-to-feishu/scripts/sync_ai_hotspot_to_feishu.py --limit 15 --hours 48 --summary-depth detailed
```

如果只要快速摘要：

```bash
python .opencode/skills/ai-hotspot-to-feishu/scripts/sync_ai_hotspot_to_feishu.py --summary-depth simple --skip-content-fetch
```

## 4. 定时任务示例

Windows（每天 12:00）：

```powershell
powershell -ExecutionPolicy Bypass -File .opencode/skills/ai-hotspot-to-feishu/scripts/register_daily_noon_task.ps1
```

Linux crontab（每天 12:00）：

```cron
0 12 * * * /usr/bin/python3 /path/to/sync_ai_hotspot_to_feishu.py --summary-depth detailed
```
