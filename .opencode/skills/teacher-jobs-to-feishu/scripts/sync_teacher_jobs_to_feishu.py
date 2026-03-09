import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.error
import urllib.request
import uuid


DEFAULT_CITIES = ["广州", "惠州", "深圳", "东莞"]
DEFAULT_LEVELS = ["初中", "高中"]
DEFAULT_SUBJECT = "生物"
DEFAULT_SUBJECT_ALIASES = ["生物", "生物学", "生命科学", "生物教师", "生物学科", "生物教研员"]
DEFAULT_LOOKBACK_DAYS = 365
DEFAULT_MAX_ITEMS = 50
DEFAULT_DETAIL_FETCH_LIMIT = 20
DEFAULT_TABLE_SCORE_THRESHOLD = 6
DEFAULT_MIN_BIOLOGY_ONLY_COUNT = 5
DEFAULT_MIN_TOTAL_WITH_FALLBACK = 12

DEFAULT_RECRUIT_KEYWORDS = [
    "招聘",
    "诚聘",
    "急聘",
    "公开招聘",
    "招聘公告",
    "招聘简章",
    "招聘岗位",
    "岗位表",
    "事业单位",
    "编制",
    "报名",
    "资格审查",
    "笔试",
    "面试",
]
DEFAULT_TEACHER_KEYWORDS = ["教师", "老师", "学科教师", "中学教师", "高中教师", "初中教师", "教研员"]
DEFAULT_BIANZHI_KEYWORDS = ["编制", "事业编", "事业单位", "事业单位公开招聘", "教师编", "入编"]
DEFAULT_EXCLUDE_KEYWORDS = [
    "研学",
    "夏令营",
    "讲座",
    "培训",
    "论坛",
    "比赛",
    "活动通知",
    "宣讲",
    "教师资格认定",
    "教师资格考试",
    "教资",
    "证书领取",
    "职称评审",
    "评优",
    "表彰",
    "招标",
    "采购",
    "中标",
    "录取名单",
    "录用名单",
    "拟聘用名单",
    "拟录用名单",
    "聘用名单",
    "聘用人员公示",
    "拟聘用人员公示",
    "录取人员公示",
    "录用人员公示",
    "公示",
    "政策",
    "法规",
    "政策解读",
    "意见征集",
    "征求意见",
    "面试公告",
    "面试通知",
    "资格复审",
    "成绩公布",
    "笔试成绩",
    "面试成绩",
]

HEADER_KEYWORDS = {
    "position": ["岗位", "职位", "招聘岗位", "岗位名称", "学科岗位", "任教学科"],
    "subject": ["学科", "科目", "专业", "任教学科", "报考学科"],
    "level": ["学段", "学部", "岗位类别", "任教阶段", "初中", "高中"],
    "district": ["区", "区县", "行政区", "单位", "学校", "招聘单位"],
    "job_code": ["岗位代码", "职位代码", "岗位编号", "代码", "职位编号"],
}

JOB_CODE_PATTERNS = [
    re.compile(r"\b[A-Za-z]{1,4}\d{3,8}[A-Za-z]?\b"),
    re.compile(r"\b\d{5,10}\b"),
]

RE_PHONE = re.compile(r"^1[3-9]\d{9}$")
RE_ID18 = re.compile(r"^\d{17}[\dXx]$")
RE_DATE_TEXT = re.compile(r"^(19|20)\d{2}[-/.年]\d{1,2}([-/月.日]\d{1,2})?")


def load_dotenv(dotenv_path):
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def make_ssl_fallback_context():
    insecure_context = ssl._create_unverified_context()
    if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
        insecure_context.options |= ssl.OP_LEGACY_SERVER_CONNECT
    try:
        insecure_context.set_ciphers("DEFAULT@SECLEVEL=1")
    except Exception:
        pass
    return insecure_context


def http_bytes(url, timeout=20):
    req = urllib.request.Request(
        url=url,
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as error:
        message = str(error)
        ssl_related = (
            "CERTIFICATE_VERIFY_FAILED" in message
            or "UNSAFE_LEGACY_RENEGOTIATION_DISABLED" in message
            or "BAD_ECPOINT" in message
        )
        if not ssl_related:
            raise

        if url.lower().startswith("https://www.baoan.gov.cn/"):
            fallback_url = "http://" + url[len("https://") :]
            fallback_req = urllib.request.Request(
                url=fallback_url,
                method="GET",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "*/*",
                },
            )
            with urllib.request.urlopen(fallback_req, timeout=timeout) as resp:
                return resp.read()

        insecure_context = make_ssl_fallback_context()
        with urllib.request.urlopen(req, timeout=timeout, context=insecure_context) as resp:
            return resp.read()


def http_text(url, timeout=20):
    data = http_bytes(url, timeout=timeout)

    meta_match = re.search(
        rb"<meta[^>]+charset=[\"']?([a-zA-Z0-9_-]+)",
        data,
        flags=re.IGNORECASE,
    )
    encodings = []
    if meta_match:
        encodings.append(meta_match.group(1).decode("ascii", errors="ignore"))
    encodings.extend(["utf-8", "gb18030", "gbk"])

    tried = set()
    for encoding in encodings:
        if not encoding:
            continue
        key = encoding.lower()
        if key in tried:
            continue
        tried.add(key)
        try:
            return data.decode(encoding, errors="strict")
        except Exception:
            continue

    return data.decode("utf-8", errors="ignore")


def http_json(method, url, data=None, headers=None, timeout=20):
    if headers is None:
        headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url=url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {error.code} | {body}") from error


def strip_html(raw):
    if not raw:
        return ""
    text = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(text):
    return re.sub(r"\s+", "", text or "")


def parse_date(text):
    if not text:
        return None
    patterns = [
        r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})\s*(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?",
        r"(20\d{2})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2})?[时:](\d{1,2})?([分:]\d{1,2})?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        groups = match.groups()
        y, m, d = groups[0], groups[1], groups[2]
        hh = groups[3] if len(groups) > 3 else None
        mm = groups[4] if len(groups) > 4 else None
        ss_raw = groups[5] if len(groups) > 5 else None
        ss = None
        if ss_raw:
            ss = ss_raw.replace("分", "").replace(":", "")
        try:
            return dt.datetime(
                int(y),
                int(m),
                int(d),
                int(hh or 0),
                int(mm or 0),
                int(ss or 0),
                tzinfo=dt.timezone.utc,
            )
        except ValueError:
            continue
    return None


def extract_publish_date_from_html(html):
    if not html:
        return None

    candidate_patterns = [
        r"published[_-]?time\"\s*content=\"([^\"]+)\"",
        r"pubdate\"\s*content=\"([^\"]+)\"",
        r"发布时间[：:]\s*([^<\n\r]{6,40})",
        r"发布日期[：:]\s*([^<\n\r]{6,40})",
        r"发文日期[：:]\s*([^<\n\r]{6,40})",
        r"时间[：:]\s*(20\d{2}[./-]\d{1,2}[./-]\d{1,2}[^<\n\r]*)",
    ]

    for pattern in candidate_patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if not match:
            continue
        parsed = parse_date(match.group(1))
        if parsed:
            return parsed

    text = strip_html(html)[:12000]
    return parse_date(text)


def get_feishu_tenant_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": app_id, "app_secret": app_secret}
    resp = http_json("POST", url, data=data)
    if resp.get("code") != 0:
        raise RuntimeError(f"获取飞书 tenant_access_token 失败: {resp}")
    return resp["tenant_access_token"]


def parse_bitable_info_from_url(url):
    if not url:
        return None, None
    parsed = urllib.parse.urlparse(url)
    full = f"{parsed.path}?{parsed.query}"
    app_match = re.search(r"(app[0-9A-Za-z]+)", full)
    table_match = re.search(r"(tbl[0-9A-Za-z]+)", full)
    app_token = app_match.group(1) if app_match else None
    table_id = table_match.group(1) if table_match else None
    return app_token, table_id


def resolve_bitable_from_wiki(wiki_url, headers):
    parsed = urllib.parse.urlparse(wiki_url)
    match = re.search(r"/wiki/([A-Za-z0-9]+)", parsed.path)
    if not match:
        raise RuntimeError("无法从 FEISHU_WIKI_URL 解析 wiki token")
    wiki_token = match.group(1)
    api = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token={wiki_token}"
    resp = http_json("GET", api, headers=headers)
    if resp.get("code") != 0:
        raise RuntimeError(f"读取 wiki 节点失败: {resp}")
    node = resp.get("data", {}).get("node", {})
    obj_type = node.get("obj_type")
    obj_token = node.get("obj_token")
    if obj_type != "bitable":
        raise RuntimeError(f"wiki 节点不是多维表格，obj_type={obj_type}")
    return obj_token


def list_bitable_tables(app_token, headers):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables?page_size=200"
    resp = http_json("GET", url, headers=headers)
    if resp.get("code") != 0:
        raise RuntimeError(f"读取多维表格数据表失败: {resp}")
    return resp.get("data", {}).get("items", [])


def list_table_fields(app_token, table_id, headers):
    url = (
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        "?page_size=500"
    )
    resp = http_json("GET", url, headers=headers)
    if resp.get("code") != 0:
        raise RuntimeError(f"读取数据表字段失败: {resp}")
    return resp.get("data", {}).get("items", [])


def create_record(app_token, table_id, headers, fields):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    payload = {"fields": fields}
    resp = http_json("POST", url, data=payload, headers=headers)
    if resp.get("code") != 0:
        raise RuntimeError(f"写入记录失败: {resp}")


def upload_file_to_feishu_bitable(headers, app_token, file_path):
    file_name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        data = f.read()

    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    parts = []

    def add_field(key, value):
        parts.append(
            (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{key}\"\r\n\r\n"
                f"{value}\r\n"
            ).encode("utf-8")
        )

    add_field("file_name", file_name)
    add_field("parent_type", "bitable_file")
    add_field("parent_node", app_token)
    add_field("size", str(len(data)))

    parts.append(
        (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{file_name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(data)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    body = b"".join(parts)
    req = urllib.request.Request(
        url="https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
        method="POST",
        data=body,
        headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if payload.get("code") != 0:
        raise RuntimeError(f"上传附件失败: {payload}")
    token = payload.get("data", {}).get("file_token")
    if not token:
        raise RuntimeError(f"上传附件未返回 file_token: {payload}")
    return token


def build_job_attachment_file(job, output_dir):
    ensure_parent_dir(os.path.join(output_dir, "placeholder.txt"))
    digest = hashlib.sha256(job.get("url", "").encode("utf-8")).hexdigest()[:16]
    file_path = os.path.join(output_dir, f"job_{digest}.txt")
    content = (
        f"岗位标题: {job.get('title', '')}\n"
        f"地区: {job.get('city', '')}\n"
        f"区县: {job.get('district', '')}\n"
        f"学段: {job.get('level', '')}\n"
        f"学科: {job.get('subject', '')}\n"
        f"发布时间: {job.get('published_at_text', '')}\n"
        f"公告链接: {job.get('url', '')}\n"
        f"匹配说明: {job.get('match_reason', '')}\n"
        f"匹配证据: {job.get('evidence', '')}\n"
    )
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def pick_field_name(field_names, candidates):
    normalized = {normalize_text(name): name for name in field_names}
    for candidate in candidates:
        key = normalize_text(candidate)
        if key in normalized:
            return normalized[key]
    for name in field_names:
        for candidate in candidates:
            if normalize_text(candidate) in normalize_text(name):
                return name
    return None


def build_record_with_best_effort(job, field_names, fields_meta=None) -> dict[str, object]:
    mapping = {
        "title": ["岗位标题", "标题", "岗位", "职位", "职位名称"],
        "city": ["地区", "城市", "地点"],
        "district": ["区县", "区", "行政区"],
        "level": ["学段", "学段要求"],
        "subject": ["学科", "科目", "学科要求"],
        "url": ["岗位链接", "公告链接", "链接", "网址", "原文链接"],
        "source": ["来源网站", "来源", "公告来源"],
        "published": ["岗位信息发布时间", "发布时间", "发布日期"],
        "collected": ["抓取时间", "采集时间", "同步时间"],
        "reason": ["匹配说明", "匹配理由", "备注", "说明"],
        "evidence": ["匹配证据", "岗位证据", "岗位明细"],
    }
    values = {
        "title": job["title"],
        "city": job["city"],
        "district": job.get("district", ""),
        "level": job["level"],
        "subject": job["subject"],
        "url": job["url"],
        "source": job["source_name"],
        "published": job["published_at_text"],
        "collected": job["collected_at"],
        "reason": job["match_reason"],
        "evidence": job.get("evidence", ""),
    }
    field_type_by_name = {}
    if fields_meta:
        field_type_by_name = {x.get("field_name"): x.get("type") for x in fields_meta if x.get("field_name")}

    result = {}  # type: dict[str, object]
    for key, candidates in mapping.items():
        chosen = pick_field_name(field_names, candidates)
        if chosen:
            value = values[key]
            ftype = field_type_by_name.get(chosen)
            if ftype == 15 and key == "url":
                value = {"link": str(values[key])}
            elif ftype == 5:
                published_at = job.get("published_at")
                if isinstance(published_at, dt.datetime):
                    value = int(published_at.timestamp() * 1000)
                else:
                    continue
            result[chosen] = value
    if result:
        return result

    if fields_meta:
        type_map = {}
        for field in fields_meta:
            ftype = field.get("type")
            fname = field.get("field_name")
            if ftype is None or not fname:
                continue
            type_map.setdefault(ftype, []).append(fname)

        typed_result = {}  # type: dict[str, object]
        text_fields = type_map.get(1, [])
        single_select_fields = type_map.get(3, [])
        date_fields = type_map.get(5, [])

        if text_fields:
            typed_result[text_fields[0]] = f"{job['title']} | {job['url']}"
        if single_select_fields:
            typed_result[single_select_fields[0]] = job.get("city", "")
        if date_fields:
            published_at = job.get("published_at")
            if isinstance(published_at, dt.datetime):
                typed_result[date_fields[0]] = int(published_at.timestamp() * 1000)

        if typed_result:
            return typed_result

    fallback_name = field_names[0] if field_names else "内容"
    fallback_value = (
        f"{job['title']} | {job['city']} | {job.get('district', '')} | {job['level']} | {job['subject']} | "
        f"{job['published_at_text']} | {job['url']}"
    )
    fallback_result: dict[str, object] = {fallback_name: fallback_value}
    return fallback_result


def read_sources(source_config_path):
    with open(source_config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise RuntimeError("采集源配置必须是 JSON 数组")
    cleaned = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        url = (item.get("url") or "").strip()
        city = (item.get("city") or "").strip()
        source_type = (item.get("type") or "html").strip().lower()
        if not name or not url:
            continue
        cleaned.append({"name": name, "url": url, "city": city, "type": source_type})
    if not cleaned:
        raise RuntimeError("采集源配置为空")
    return cleaned


def extract_html_links(page_html, base_url):
    if not page_html:
        return []
    links = []
    pattern = re.compile(r"<a\b[^>]*href=[\"']?([^\"' >]+)[\"']?[^>]*>([\s\S]*?)</a>", re.IGNORECASE)
    for href, text_html in pattern.findall(page_html):
        href = href.strip()
        if not href:
            continue
        title = strip_html(text_html)
        if len(title) < 6:
            continue
        if "function(" in title or "append(" in title or "$('#" in title:
            continue
        if href.lower().startswith("javascript:"):
            continue
        if href.startswith("#"):
            continue
        url = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(url)
        if (parsed.path or "/") == "/" and not parsed.query:
            continue
        links.append({"title": title, "url": url})
    dedup = {}
    for item in links:
        if item["url"] not in dedup:
            dedup[item["url"]] = item
    return list(dedup.values())


def extract_pagination_urls(page_html, base_url, max_pages):
    if not page_html:
        return []
    links = []
    for href in re.findall(r"href=[\"']([^\"']*index(?:_\d+)?\.html)[\"']", page_html, flags=re.IGNORECASE):
        url = urllib.parse.urljoin(base_url, href.strip())
        if url not in links:
            links.append(url)
    return links[:max_pages]


def extract_baoan_links_with_dates(page_html, base_url):
    if not page_html:
        return []
    items = []
    pattern = re.compile(
        r"<a[^>]*href=[\"']([^\"']*?/content/post_\d+\.html)[\"'][^>]*>([\s\S]*?)</a>[\s\S]{0,2000}?发布日期\s*[：:]\s*(20\d{2}-\d{2}-\d{2})",
        flags=re.IGNORECASE,
    )
    for href, title_html, date_text in pattern.findall(page_html):
        title = strip_html(title_html)
        if not title:
            continue
        items.append(
            {
                "title": title,
                "url": urllib.parse.urljoin(base_url, href.strip()).replace(
                    "https://www.baoan.gov.cn/", "http://www.baoan.gov.cn/"
                ),
                "published_at": parse_date(date_text),
            }
        )

    dedup = {}
    for item in items:
        if item["url"] not in dedup:
            dedup[item["url"]] = item
    return list(dedup.values())


def is_table_attachment(url):
    lower = urllib.parse.urlparse(url).path.lower()
    return lower.endswith(".xlsx") or lower.endswith(".xls") or lower.endswith(".csv")


def extract_table_attachments(page_html, base_url):
    attachments = []
    for link in extract_html_links(page_html, base_url):
        url = link.get("url", "")
        if is_table_attachment(url):
            attachments.append({"title": link.get("title", "附件表格"), "url": url})
    return attachments


def fetch_source_items(source, timeout):
    source_type = source.get("type", "html")
    url = source["url"]
    items = []
    if source_type == "html":
        html_text = http_text(url, timeout=timeout)
        links = extract_html_links(html_text, url)
        is_baoan_ryzp = "baoan.gov.cn/jyj/zwgk/rsxx/ryzp" in url.lower()
        baoan_items = extract_baoan_links_with_dates(html_text, url) if is_baoan_ryzp else []

        max_list_pages = int(os.getenv("MAX_LIST_PAGES", "6"))
        pagination_urls = extract_pagination_urls(html_text, url, max_pages=max_list_pages)
        for page_url in pagination_urls:
            if page_url == url:
                continue
            try:
                page_html = http_text(page_url, timeout=timeout)
                links.extend(extract_html_links(page_html, page_url))
                if is_baoan_ryzp:
                    baoan_items.extend(extract_baoan_links_with_dates(page_html, page_url))
            except Exception:
                continue

        if baoan_items:
            merged = {}
            for item in baoan_items:
                merged[item["url"]] = item
            for item in merged.values():
                items.append(
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "published_at": item.get("published_at"),
                        "source_name": source["name"],
                        "source_city": source.get("city", ""),
                    }
                )
            return items

        for link in links:
            text = link["title"]
            pub = parse_date(text)
            items.append(
                {
                    "title": text,
                    "url": link["url"],
                    "published_at": pub,
                    "source_name": source["name"],
                    "source_city": source.get("city", ""),
                }
            )
    else:
        raise RuntimeError(f"暂不支持的 source type: {source_type}")
    return items


def contains_any(text, words):
    return any(word in text for word in words)


def matches_subject(text, subject_aliases):
    return any(alias in text for alias in subject_aliases)


def is_teacher_recruitment_text(
    text,
    recruit_keywords,
    teacher_keywords,
    bianzhi_keywords,
    exclude_keywords,
    force_teacher_channel=False,
):
    if not text:
        return False
    has_teacher = contains_any(text, teacher_keywords)
    has_recruit = contains_any(text, recruit_keywords)
    has_bianzhi = contains_any(text, bianzhi_keywords)
    has_public_recruit = contains_any(text, ["公开招聘", "事业单位", "校园招聘"])
    if force_teacher_channel:
        return has_teacher and has_recruit
    return has_teacher and has_recruit and (has_bianzhi or has_public_recruit)


def build_subject_aliases(target_subject, extra_aliases):
    aliases = []
    for value in [target_subject] + DEFAULT_SUBJECT_ALIASES + list(extra_aliases):
        candidate = normalize_text(value)
        if candidate and candidate not in aliases:
            aliases.append(candidate)
    return aliases


def classify_level(text):
    if "高中" in text:
        return "高中"
    if "初中" in text:
        return "初中"
    if "中学" in text:
        return "中学"
    return "未标注"


def infer_city(text, source_city, target_cities):
    for city in target_cities:
        if city in text:
            return city
    if source_city in target_cities:
        return source_city
    return source_city or "未标注"


def infer_district(text, target_districts):
    if not target_districts:
        return ""
    for district in target_districts:
        if district in text:
            return district
    return ""


def ensure_parent_dir(path):
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def download_attachment(url, attachment_dir, timeout):
    parsed = urllib.parse.urlparse(url)
    suffix = os.path.splitext(parsed.path)[1].lower() or ".bin"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:18]
    file_path = os.path.join(attachment_dir, f"{digest}{suffix}")
    if os.path.exists(file_path):
        return file_path
    ensure_parent_dir(file_path)
    data = http_bytes(url, timeout=timeout)
    with open(file_path, "wb") as f:
        f.write(data)
    return file_path


def flatten_row_to_text(values):
    normalized = []
    for v in values:
        if v is None:
            continue
        text = str(v).strip()
        if text:
            normalized.append(text)
    return " | ".join(normalized)


def normalize_row(values):
    return [str(v).strip() if v is not None else "" for v in values]


def find_header_row(rows, search_rows=8):
    best_index = 0
    best_score = -1
    limit = min(len(rows), search_rows)
    for idx in range(limit):
        row = rows[idx]
        score = 0
        for cell in row:
            token = normalize_text(cell)
            if not token:
                continue
            for keywords in HEADER_KEYWORDS.values():
                if any(normalize_text(k) in token for k in keywords):
                    score += 1
                    break
        if score > best_score:
            best_score = score
            best_index = idx
    return best_index


def build_header_map(header_row):
    mapping = {"position": [], "subject": [], "level": [], "district": [], "job_code": []}
    for idx, cell in enumerate(header_row):
        token = normalize_text(cell)
        if not token:
            continue
        for key, keywords in HEADER_KEYWORDS.items():
            if any(normalize_text(k) in token for k in keywords):
                mapping[key].append(idx)
    return mapping


def cells_by_indexes(row, indexes):
    out = []
    for i in indexes:
        if 0 <= i < len(row):
            text = row[i].strip()
            if text:
                out.append(text)
    return out


def has_job_code(text):
    if not text:
        return False
    candidate = text.strip()
    if RE_PHONE.match(candidate) or RE_ID18.match(candidate) or RE_DATE_TEXT.match(candidate):
        return False
    return any(pattern.search(candidate) for pattern in JOB_CODE_PATTERNS)


def evaluate_row_score(
    row,
    row_text,
    header_map,
    subject_aliases,
    target_levels,
    target_districts,
):
    score = 0
    reasons = []

    subject_cols = cells_by_indexes(row, header_map["subject"])
    level_cols = cells_by_indexes(row, header_map["level"])
    district_cols = cells_by_indexes(row, header_map["district"])
    position_cols = cells_by_indexes(row, header_map["position"])
    code_cols = cells_by_indexes(row, header_map["job_code"])

    subject_text = normalize_text(" ".join(subject_cols))
    level_text = normalize_text(" ".join(level_cols))
    district_text = normalize_text(" ".join(district_cols))
    position_text = normalize_text(" ".join(position_cols))
    code_text = " ".join(code_cols)

    if subject_cols and matches_subject(subject_text, subject_aliases):
        score += 5
        reasons.append("学科列")
    elif matches_subject(normalize_text(row_text), subject_aliases):
        score += 2
        reasons.append("整行学科")

    if contains_any(level_text, list(target_levels) + ["中学"]):
        score += 3
        reasons.append("学段列")
    elif contains_any(normalize_text(row_text), list(target_levels) + ["中学"]):
        score += 1
        reasons.append("整行学段")

    if target_districts:
        if district_cols and contains_any(district_text, target_districts):
            score += 2
            reasons.append("区县列")
        elif contains_any(normalize_text(row_text), target_districts):
            score += 1
            reasons.append("整行区县")

    if contains_any(position_text, ["教师", "教研员", "生物", "学科"]):
        score += 2
        reasons.append("岗位列")

    if has_job_code(code_text):
        score += 2
        reasons.append("代码列")
    elif has_job_code(row_text):
        score += 1
        reasons.append("整行代码")

    return score, reasons


def extract_table_matches_from_rows(
    rows,
    sheet_name,
    subject_aliases,
    target_levels,
    target_districts,
    score_threshold,
    max_lines,
):
    normalized_rows = [normalize_row(r) for r in rows if flatten_row_to_text(r)]
    if not normalized_rows:
        return []

    header_index = find_header_row(normalized_rows)
    header_map = build_header_map(normalized_rows[header_index])
    matched = []

    for row in normalized_rows[header_index + 1 :]:
        row_text = flatten_row_to_text(row)
        if not row_text:
            continue
        score, reasons = evaluate_row_score(
            row=row,
            row_text=row_text,
            header_map=header_map,
            subject_aliases=subject_aliases,
            target_levels=target_levels,
            target_districts=target_districts,
        )
        if score < score_threshold:
            continue
        reason_text = "+".join(reasons) if reasons else "规则命中"
        matched.append(f"[{sheet_name}] score={score} reason={reason_text} | {row_text}")
        if len(matched) >= max_lines:
            break
    return matched


def read_csv_matches(
    file_path,
    subject_aliases,
    target_levels,
    target_districts,
    score_threshold,
    max_lines=8,
):
    rows = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
            if len(rows) >= 1200:
                break
    return extract_table_matches_from_rows(
        rows=rows,
        sheet_name="CSV",
        subject_aliases=subject_aliases,
        target_levels=target_levels,
        target_districts=target_districts,
        score_threshold=score_threshold,
        max_lines=max_lines,
    )


def read_xlsx_matches(
    file_path,
    subject_aliases,
    target_levels,
    target_districts,
    score_threshold,
    max_lines=8,
):
    try:
        import openpyxl
    except Exception:
        return []

    matched = []
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append(list(row))
            if len(rows) >= 1200:
                break
        sheet_matches = extract_table_matches_from_rows(
            rows=rows,
            sheet_name=ws.title,
            subject_aliases=subject_aliases,
            target_levels=target_levels,
            target_districts=target_districts,
            score_threshold=score_threshold,
            max_lines=max_lines,
        )
        matched.extend(sheet_matches)
        if len(matched) >= max_lines:
            wb.close()
            return matched[:max_lines]
    wb.close()
    return matched[:max_lines]


def read_xls_matches(
    file_path,
    subject_aliases,
    target_levels,
    target_districts,
    score_threshold,
    max_lines=8,
):
    try:
        import xlrd
    except Exception:
        return []

    matched = []
    book = xlrd.open_workbook(file_path)
    for sheet in book.sheets():
        rows = []
        for r in range(sheet.nrows):
            rows.append(sheet.row_values(r))
            if len(rows) >= 1200:
                break
        sheet_matches = extract_table_matches_from_rows(
            rows=rows,
            sheet_name=sheet.name,
            subject_aliases=subject_aliases,
            target_levels=target_levels,
            target_districts=target_districts,
            score_threshold=score_threshold,
            max_lines=max_lines,
        )
        matched.extend(sheet_matches)
        if len(matched) >= max_lines:
            return matched[:max_lines]
    return matched[:max_lines]


def extract_table_matches(file_path, subject_aliases, target_levels, target_districts, score_threshold):
    lower = file_path.lower()
    if lower.endswith(".csv"):
        return read_csv_matches(
            file_path,
            subject_aliases,
            target_levels,
            target_districts,
            score_threshold,
        )
    if lower.endswith(".xlsx"):
        return read_xlsx_matches(
            file_path,
            subject_aliases,
            target_levels,
            target_districts,
            score_threshold,
        )
    if lower.endswith(".xls"):
        return read_xls_matches(
            file_path,
            subject_aliases,
            target_levels,
            target_districts,
            score_threshold,
        )
    return []


def fetch_detail_evidence(
    item,
    timeout,
    attachment_dir,
    subject_aliases,
    target_levels,
    target_districts,
    score_threshold,
):
    try:
        detail_html = http_text(item["url"], timeout=timeout)
    except Exception:
        return "", "", None, []

    detail_text = strip_html(detail_html)[:30000]
    detail_published_at = extract_publish_date_from_html(detail_html)
    attachment_lines = []
    attachment_files = []
    attachments = extract_table_attachments(detail_html, item["url"])
    for attachment in attachments:
        try:
            local_file = download_attachment(attachment["url"], attachment_dir, timeout=timeout)
            attachment_files.append(local_file)
            rows = extract_table_matches(
                local_file,
                subject_aliases,
                target_levels,
                target_districts,
                score_threshold,
            )
            if rows:
                attachment_lines.extend(rows[:4])
        except Exception:
            continue

    attachment_text = "\n".join(attachment_lines)
    return detail_text, attachment_text, detail_published_at, attachment_files


def build_match_reason(city, district, level, subject, used_detail, used_table):
    parts = [f"命中地区={city}"]
    if district:
        parts.append(f"区县={district}")
    parts.append(f"学段={level}")
    parts.append(f"学科={subject}")
    if used_table:
        parts.append("证据=表格")
    elif used_detail:
        parts.append("证据=正文")
    else:
        parts.append("证据=标题")
    return "，".join(parts)


def filter_jobs(
    items,
    target_cities,
    target_levels,
    target_subject,
    subject_aliases,
    target_districts,
    lookback_days,
    max_items,
    timeout,
    attachment_dir,
    detail_fetch_limit,
    table_score_threshold,
    debug_stats,
    recruit_keywords,
    teacher_keywords,
    bianzhi_keywords,
    exclude_keywords,
    min_biology_only_count,
    min_total_with_fallback,
):
    now = dt.datetime.now(dt.timezone.utc)
    min_time = now - dt.timedelta(days=lookback_days)
    result = []
    seen = set()
    detail_count = 0

    recruit_keywords = [normalize_text(x) for x in recruit_keywords if normalize_text(x)]
    teacher_keywords = [normalize_text(x) for x in teacher_keywords if normalize_text(x)]
    bianzhi_keywords = [normalize_text(x) for x in bianzhi_keywords if normalize_text(x)]
    exclude_keywords = [normalize_text(x) for x in exclude_keywords if normalize_text(x)]
    precheck_words = list(dict.fromkeys(recruit_keywords + teacher_keywords + bianzhi_keywords))
    target_levels_set = set(target_levels)
    counters = {
        "total_items": 0,
        "precheck_pass": 0,
        "date_pass": 0,
        "subject_pass": 0,
        "level_pass": 0,
        "city_pass": 0,
        "district_pass": 0,
        "dedup_pass": 0,
        "matched": 0,
        "fallback_teacher_matched": 0,
    }

    biology_jobs = []
    fallback_teacher_jobs = []

    for item in items:
        counters["total_items"] += 1
        title = item.get("title", "")
        title_text = normalize_text(title)
        if not contains_any(title_text, precheck_words):
            continue
        if contains_any(title_text, exclude_keywords):
            continue

        title_has_recruit = contains_any(title_text, recruit_keywords)
        title_has_teacher = contains_any(title_text, teacher_keywords) or ("学校" in title_text)
        if not (title_has_recruit and title_has_teacher):
            continue
        counters["precheck_pass"] += 1

        published_at = item.get("published_at")
        if published_at and published_at < min_time:
            continue
        counters["date_pass"] += 1

        detail_text = ""
        table_text = ""
        detail_published_at = None
        attachment_files = []
        if detail_count < detail_fetch_limit:
            detail_count += 1
            detail_text, table_text, detail_published_at, attachment_files = fetch_detail_evidence(
                item=item,
                timeout=timeout,
                attachment_dir=attachment_dir,
                subject_aliases=subject_aliases,
                target_levels=target_levels,
                target_districts=target_districts,
                score_threshold=table_score_threshold,
            )

        if detail_published_at:
            published_at = detail_published_at
        if published_at and published_at < min_time:
            continue
        if published_at is None:
            continue

        merged_text = normalize_text(f"{title} {detail_text} {table_text}")
        is_teacher_channel = "/ryzp/" in (item.get("url", "") or "")
        if not is_teacher_recruitment_text(
            merged_text,
            recruit_keywords,
            teacher_keywords,
            bianzhi_keywords,
            exclude_keywords,
            force_teacher_channel=is_teacher_channel,
        ):
            continue

        is_biology = matches_subject(merged_text, subject_aliases)
        if is_biology:
            counters["subject_pass"] += 1
        elif not target_subject:
            continue

        level = classify_level(merged_text)
        if is_biology:
            if level == "中学":
                level_ok = bool(target_levels_set.intersection({"初中", "高中"}))
            else:
                level_ok = level in target_levels_set
            if not level_ok:
                continue
        counters["level_pass"] += 1

        city = infer_city(merged_text, item.get("source_city", ""), target_cities)
        if city not in target_cities:
            continue
        counters["city_pass"] += 1

        district = infer_district(merged_text, target_districts)
        if target_districts and not district:
            continue
        counters["district_pass"] += 1

        url = item.get("url", "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        counters["dedup_pass"] += 1

        evidence = ""
        if table_text:
            evidence = table_text[:1200]
        elif detail_text:
            evidence = detail_text[:300]

        job = {
            "title": title,
            "city": city,
            "district": district,
            "level": level,
            "subject": target_subject if is_biology else "教师招聘（非生物）",
            "url": url,
            "source_name": item.get("source_name", ""),
            "published_at": published_at,
            "published_at_text": (
                published_at.astimezone(dt.datetime.now().astimezone().tzinfo).strftime("%Y-%m-%d")
                if published_at
                else "未知"
            ),
            "collected_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "match_reason": build_match_reason(
                city=city,
                district=district,
                level=level,
                subject=(target_subject if is_biology else "教师招聘"),
                used_detail=bool(detail_text),
                used_table=bool(table_text),
            ),
            "evidence": evidence,
            "attachment_files": attachment_files,
        }
        if is_biology:
            biology_jobs.append(job)
            counters["matched"] += 1
        else:
            fallback_teacher_jobs.append(job)
            counters["fallback_teacher_matched"] += 1

    if debug_stats:
        print(
            "[DEBUG] "
            + " ".join(
                [
                    f"total={counters['total_items']}",
                    f"precheck={counters['precheck_pass']}",
                    f"date={counters['date_pass']}",
                    f"subject={counters['subject_pass']}",
                    f"level={counters['level_pass']}",
                    f"city={counters['city_pass']}",
                    f"district={counters['district_pass']}",
                    f"dedup={counters['dedup_pass']}",
                    f"matched={counters['matched']}",
                    f"fallback_teacher={counters['fallback_teacher_matched']}",
                    f"detail_fetch={detail_count}",
                ]
            )
        )

    if biology_jobs and len(biology_jobs) >= min_biology_only_count:
        result = list(biology_jobs)
        if len(result) < min_total_with_fallback:
            needed = max(0, min_total_with_fallback - len(result))
            result.extend(fallback_teacher_jobs[:needed])
    elif biology_jobs:
        result = biology_jobs + fallback_teacher_jobs
    else:
        result = fallback_teacher_jobs

    result.sort(
        key=lambda x: x.get("published_at") or dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc),
        reverse=True,
    )
    return result[:max_items]


def load_seen_urls(file_path):
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return set(str(x) for x in data)
        return set()
    except Exception:
        return set()


def save_seen_urls(file_path, urls):
    ensure_parent_dir(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, ensure_ascii=False, indent=2)


def parse_args():
    parser = argparse.ArgumentParser(description="抓取教师岗位并写入飞书多维表格")
    parser.add_argument("--max-items", type=int, default=int(os.getenv("MAX_ITEMS", str(DEFAULT_MAX_ITEMS))))
    parser.add_argument(
        "--lookback-days", type=int, default=int(os.getenv("LOOKBACK_DAYS", str(DEFAULT_LOOKBACK_DAYS)))
    )
    parser.add_argument(
        "--detail-fetch-limit",
        type=int,
        default=int(os.getenv("DETAIL_FETCH_LIMIT", str(DEFAULT_DETAIL_FETCH_LIMIT))),
    )
    parser.add_argument(
        "--table-score-threshold",
        type=int,
        default=int(os.getenv("TABLE_SCORE_THRESHOLD", str(DEFAULT_TABLE_SCORE_THRESHOLD))),
    )
    parser.add_argument(
        "--min-biology-only-count",
        type=int,
        default=int(os.getenv("MIN_BIOLOGY_ONLY_COUNT", str(DEFAULT_MIN_BIOLOGY_ONLY_COUNT))),
    )
    parser.add_argument(
        "--min-total-with-fallback",
        type=int,
        default=int(os.getenv("MIN_TOTAL_WITH_FALLBACK", str(DEFAULT_MIN_TOTAL_WITH_FALLBACK))),
    )
    parser.add_argument(
        "--source-config",
        type=str,
        default=os.getenv(
            "JOB_SOURCE_CONFIG",
            ".opencode/skills/teacher-jobs-to-feishu/references/sources_template.json",
        ),
    )
    parser.add_argument("--debug-stats", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def parse_comma_env(name, default_list):
    value = os.getenv(name, "")
    if not value.strip():
        return default_list
    return [x.strip() for x in value.split(",") if x.strip()]


def resolve_bitable_tokens(headers):
    app_token = os.getenv("FEISHU_BITABLE_APP_TOKEN")
    table_id = os.getenv("FEISHU_BITABLE_TABLE_ID")
    if app_token:
        return app_token, table_id

    bitable_url = os.getenv("FEISHU_BITABLE_URL", "")
    app_from_url, table_from_url = parse_bitable_info_from_url(bitable_url)
    if app_from_url:
        return app_from_url, table_id or table_from_url

    wiki_url = os.getenv("FEISHU_WIKI_URL", "")
    if wiki_url:
        app_from_wiki = resolve_bitable_from_wiki(wiki_url, headers)
        return app_from_wiki, table_id

    raise RuntimeError("缺少 FEISHU_BITABLE_URL 或 FEISHU_BITABLE_APP_TOKEN")


def main():
    skill_root = os.path.dirname(os.path.dirname(__file__))
    dotenv_path = os.path.join(skill_root, ".env")
    load_dotenv(dotenv_path)

    args = parse_args()
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        raise RuntimeError("缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET")

    timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    target_cities = parse_comma_env("TARGET_CITIES", DEFAULT_CITIES)
    target_levels = parse_comma_env("TARGET_LEVELS", DEFAULT_LEVELS)
    target_subject = os.getenv("TARGET_SUBJECT", DEFAULT_SUBJECT).strip() or DEFAULT_SUBJECT
    extra_subject_aliases = parse_comma_env("TARGET_SUBJECT_ALIASES", [])
    subject_aliases = build_subject_aliases(target_subject, extra_subject_aliases)
    target_districts = parse_comma_env("TARGET_DISTRICTS", [])
    recruit_keywords = parse_comma_env("RECRUIT_KEYWORDS", DEFAULT_RECRUIT_KEYWORDS)
    teacher_keywords = parse_comma_env("TEACHER_KEYWORDS", DEFAULT_TEACHER_KEYWORDS)
    bianzhi_keywords = parse_comma_env("BIANZHI_KEYWORDS", DEFAULT_BIANZHI_KEYWORDS)
    exclude_keywords = parse_comma_env("EXCLUDE_KEYWORDS", DEFAULT_EXCLUDE_KEYWORDS)

    source_config_path = args.source_config
    if not os.path.isabs(source_config_path):
        source_config_path = os.path.join(os.getcwd(), source_config_path)
    sources = read_sources(source_config_path)
    sources = sorted(
        sources,
        key=lambda s: (
            0 if "人员招聘" in (s.get("name") or "") else 1,
            0 if "教育局" in (s.get("name") or "") else 1,
        ),
    )

    all_items = []
    for source in sources:
        try:
            all_items.extend(fetch_source_items(source, timeout=timeout))
        except Exception as error:
            print(f"[WARN] 抓取失败 {source.get('name')}: {error}")

    attachment_dir = os.path.join(skill_root, "scripts", "data", "attachments")
    jobs = filter_jobs(
        items=all_items,
        target_cities=target_cities,
        target_levels=target_levels,
        target_subject=target_subject,
        subject_aliases=subject_aliases,
        target_districts=target_districts,
        lookback_days=args.lookback_days,
        max_items=args.max_items,
        timeout=timeout,
        attachment_dir=attachment_dir,
        detail_fetch_limit=max(0, args.detail_fetch_limit),
        table_score_threshold=max(1, args.table_score_threshold),
        debug_stats=args.debug_stats,
        recruit_keywords=recruit_keywords,
        teacher_keywords=teacher_keywords,
        bianzhi_keywords=bianzhi_keywords,
        exclude_keywords=exclude_keywords,
        min_biology_only_count=max(0, args.min_biology_only_count),
        min_total_with_fallback=max(0, args.min_total_with_fallback),
    )

    seen_file = os.path.join(skill_root, "scripts", "data", "seen_jobs.json")
    already_seen = load_seen_urls(seen_file)
    jobs_new = [job for job in jobs if job["url"] not in already_seen]

    if not jobs_new:
        print("[INFO] 没有新的匹配岗位")
        return

    if args.dry_run:
        print(f"[DRY_RUN] 命中新岗位数量: {len(jobs_new)}")
        for idx, job in enumerate(jobs_new[:20], start=1):
            print(
                f"[DRY_RUN] #{idx} {job.get('published_at_text')} | {job.get('city')} | "
                f"{job.get('title')} | {job.get('url')}"
            )
        return

    tenant_token = get_feishu_tenant_token(app_id, app_secret)
    headers = {"Authorization": f"Bearer {tenant_token}"}

    app_token, table_id = resolve_bitable_tokens(headers)
    tables = list_bitable_tables(app_token, headers)
    if not tables:
        raise RuntimeError("多维表格下没有可用数据表")

    if not table_id:
        table_id = tables[0].get("table_id")
    if not table_id:
        raise RuntimeError("无法确定 FEISHU_BITABLE_TABLE_ID")

    fields_meta = list_table_fields(app_token, table_id, headers)
    field_names = [x.get("field_name") for x in fields_meta if x.get("field_name")]
    attachment_field = next((x.get("field_name") for x in fields_meta if x.get("type") == 17), None)
    upload_payload_dir = os.path.join(skill_root, "scripts", "data", "upload_payloads")

    inserted = 0
    skipped = 0
    for job in jobs_new:
        try:
            record_fields: dict[str, object] = build_record_with_best_effort(
                job,
                field_names,
                fields_meta=fields_meta,
            )
            if attachment_field:
                try:
                    attachment_tokens = []
                    for local_file in job.get("attachment_files", []):
                        file_token = upload_file_to_feishu_bitable(headers, app_token, local_file)
                        attachment_tokens.append({"file_token": file_token})

                    if not attachment_tokens:
                        payload_file = build_job_attachment_file(job, upload_payload_dir)
                        file_token = upload_file_to_feishu_bitable(headers, app_token, payload_file)
                        attachment_tokens.append({"file_token": file_token})

                    record_fields[attachment_field] = attachment_tokens
                except Exception as attach_error:
                    print(f"[WARN] 附件上传失败: {job.get('title')} | {attach_error}")
            create_record(app_token, table_id, headers, record_fields)
            inserted += 1
            already_seen.add(job["url"])
        except Exception as error:
            skipped += 1
            print(f"[WARN] 写入失败: {job.get('title')} | {error}")

    save_seen_urls(seen_file, already_seen)
    print(
        f"[OK] 完成同步 matched={len(jobs)} inserted={inserted} skipped={skipped} "
        f"table_id={table_id}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"[ERROR] {error}")
        sys.exit(1)
