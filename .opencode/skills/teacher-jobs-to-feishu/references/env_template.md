# 环境变量模板

```bash
# 飞书应用（必填）
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx

# 飞书多维表格（二选一）
# 方式1（推荐）：直接给多维表格链接
FEISHU_BITABLE_URL=https://xxx.feishu.cn/base/appxxxx?table=tblxxxx&view=vewxxxx

# 方式2：直接给 token
# FEISHU_BITABLE_APP_TOKEN=appxxxx
# FEISHU_BITABLE_TABLE_ID=tblxxxx

# 可选：若只有 wiki 链接可填，脚本会尝试解析为多维表格
# FEISHU_WIKI_URL=https://xxx.feishu.cn/wiki/xxxx

# 采集配置文件
JOB_SOURCE_CONFIG=.opencode/skills/teacher-jobs-to-feishu/references/sources_template.json

# 筛选配置
TARGET_CITIES=广州,惠州,深圳,东莞
TARGET_LEVELS=初中,高中
TARGET_SUBJECT=生物
# 可选：学科同义词扩展，提升命中率
# TARGET_SUBJECT_ALIASES=生物学,生命科学,生物学科,生物教研员
# 教师招聘过滤词（可选）
# RECRUIT_KEYWORDS=招聘,公开招聘,招聘公告,岗位,报名,资格审查,笔试,面试
# TEACHER_KEYWORDS=教师,老师,教研员,中学,高中,初中
# BIANZHI_KEYWORDS=编制,事业编,事业单位,事业单位公开招聘,教师编,入编
# EXCLUDE_KEYWORDS=研学,夏令营,讲座,培训,论坛,比赛,活动通知,宣讲,教资,资格认定
# 可选：区名白名单（填了就只保留命中区名的岗位）
# TARGET_DISTRICTS=天河区,白云区,番禺区,南山区,福田区,宝安区,龙岗区
LOOKBACK_DAYS=30
MAX_ITEMS=50
DETAIL_FETCH_LIMIT=20
# 表格规则匹配分数阈值（越高越严格）
TABLE_SCORE_THRESHOLD=6
# 列表页翻页抓取上限
MAX_LIST_PAGES=6
MIN_TOTAL_WITH_FALLBACK=12
REQUEST_TIMEOUT_SECONDS=20
```

## 安全建议

- 请不要将 `FEISHU_APP_SECRET` 写入代码或提交到仓库。
- 如果密钥已在聊天、截图或日志中暴露，请立即在飞书开放平台重置密钥并替换。
