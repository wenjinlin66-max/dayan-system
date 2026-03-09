# 使用说明

## 1) 准备飞书权限

在飞书开放平台给应用添加并开通以下权限：

- `bitable:app`
- `bitable:app:readonly`
- `wiki:node:read`

并把该应用添加到你的目标多维表格协作者中（至少可编辑）。

## 2) 准备环境变量

在 `scripts/.env` 中填入 `env_template.md` 的变量。

## 3) 调整采集源

编辑 `references/sources_template.json`，补充你重点关注的“官方招聘栏目页”。

建议优先放：

- 广州、深圳、东莞、惠州教育局
- 各区教育局
- 市/区人社局事业单位招聘栏

### 推荐监控分层（很重要）

- 第一层（强依赖，官方）：省/市/区 `gov.cn` 招聘与人事栏目
- 第二层（辅助，官方）：考试院、人社报名系统入口页
- 第三层（发现线索，非官方）：中公、华图、粉笔等聚合站

说明：第三层只用于“发现新公告线索”，最终报名与资格判断必须回到官方原文。

### 你给出的高价值入口（已纳入模板）

- 广东人事考试网：`http://rsks.gd.gov.cn/`
- 广东省人社厅事业单位公开招聘：`https://hrss.gd.gov.cn/zwgk/sydwzp/index.html`
- 深圳市考试院：`http://hrss.sz.gov.cn/szksy/`
- 深圳市教育局：`http://szeb.sz.gov.cn/`
- 广州市人社局人事考试：`http://rsj.gz.gov.cn/ywzt/rsks/`
- 广州市教育局：`http://jyj.gz.gov.cn/`
- 惠州市教育局：`http://jyj.huizhou.gov.cn/`
- 惠州市人社局：`http://rsj.huizhou.gov.cn/`
- 东莞市教育局：`https://edu.dg.gov.cn/`
- 东莞市人社局公开招聘：`https://dghrss.dg.gov.cn/xwzx/gsgg/gkzp/index.html`

### 高频区级入口（已纳入模板）

- 深圳：宝安/龙岗/南山/福田教育局
- 广州：天河/白云/番禺政府站
- 惠州：惠城区政府站

## 4) 执行脚本

```bash
python .opencode/skills/teacher-jobs-to-feishu/scripts/sync_teacher_jobs_to_feishu.py
```

常用参数：

```bash
python .opencode/skills/teacher-jobs-to-feishu/scripts/sync_teacher_jobs_to_feishu.py --max-items 30 --lookback-days 45
```

如果你希望限制到指定区县，可在 `.env` 增加：

```bash
TARGET_DISTRICTS=天河区,白云区,番禺区,南山区,福田区,宝安区,龙岗区
```

如果你希望提高生物岗位命中率，可加学科同义词：

```bash
TARGET_SUBJECT_ALIASES=生物学,生命科学,生物学科,生物教研员
```

脚本会同时匹配标题、正文、附件表格中的这些词。

## 4.2 发布时间与兜底策略

- `岗位信息发布时间` 优先取公告页真实发布时间（如“发布时间/发布日期/发文日期”），不是抓取执行时间。
- 当没有发现“生物老师”相关岗位时，脚本会自动退化为“教师招聘（非生物）”公告，避免当天无输出。
- 脚本会排除常见无关信息：研学、夏令营、培训、讲座、教资认定等。

## 4.1 岗位附件表（Excel）自动解析

- 脚本会自动进入公告正文页，查找 `.xlsx/.xls/.csv` 附件链接。
- 能下载就会下载到：`scripts/data/attachments/`。
- 对附件会做“列名识别 + 岗位代码正则 + 规则评分”扫描（学科=生物同义词 + 学段=初中/高中），命中内容会写入“匹配证据”。
- 评分阈值可调：`TABLE_SCORE_THRESHOLD`（默认 6，越高越严格）。
- 若环境缺少 Excel 解析库，脚本不会中断：
  - `.xlsx` 需要 `openpyxl`
  - `.xls` 需要 `xlrd`

安装示例：

```bash
pip install openpyxl xlrd
```

## 5) 结果说明

- 输出 `matched`：匹配岗位数
- 输出 `inserted`：成功写入多维表格数
- 输出 `skipped`：因去重或数据无效而跳过

### 关于 `[WARN] 抓取失败`

- 部分政府站会有临时 403/404、证书链或反爬限制，这在日常巡检中常见。
- 脚本设计为“单站失败不影响全局”，会继续抓取其他来源。
- 建议保留多来源冗余，不要因为单站偶发失败就只保留一个来源。

## 6) 定时执行（可选）

可用 Windows 任务计划程序每日定时执行上述命令，实现自动监控。

## 7) 聚合站（仅作线索）

- 中公广东教师招聘：`http://gd.zgjsks.com/`
- 华图广东教师招聘：`http://gd.huatu.com/jiaoshi/`
- 粉笔公告库：`https://fenbi.com/`

建议做法：聚合站看到岗位后，立即在官方站检索同标题并以官方链接为准。
