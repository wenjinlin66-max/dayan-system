import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


DEFAULT_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "llm",
    "gpt",
    "agent",
    "openai",
    "anthropic",
    "deepseek",
    "transformer",
]

DEFAULT_SOURCES = {
    "openai": "https://openai.com/news/rss.xml",
    "techcrunch_ai": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "google_ai": "https://news.google.com/rss/search?q=AI+OR+LLM+OR+OpenAI+OR+Anthropic&hl=en-US&gl=US&ceid=US:en",
}


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


def http_json(method, url, data=None, headers=None, timeout=20):
    if headers is None:
        headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url=url, method=method, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = resp.read().decode("utf-8")
        return json.loads(text)


def http_text(url, timeout=20):
    req = urllib.request.Request(url=url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_rss_time(text):
    if not text:
        return None
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    for fmt in formats:
        try:
            dt_obj = dt.datetime.strptime(text.strip(), fmt)
            if dt_obj.tzinfo is None:
                dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
            return dt_obj.astimezone(dt.timezone.utc)
        except ValueError:
            continue
    return None


def strip_html(raw):
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text):
    if not text:
        return []
    parts = re.split(r"(?<=[。！？.!?])\s+", text)
    return [p.strip() for p in parts if p and len(p.strip()) >= 18]


def is_mostly_english(text):
    if not text:
        return True
    ascii_letters = sum(1 for c in text if ("a" <= c.lower() <= "z"))
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return ascii_letters > (chinese_chars * 2 + 30)


def ai_topic_keywords_to_cn(text):
    mapping = {
        "chatgpt": "ChatGPT",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "claude": "Claude",
        "gemini": "Gemini",
        "deepseek": "DeepSeek",
        "agent": "智能体",
        "llm": "大语言模型",
        "model": "模型能力",
        "reasoning": "推理能力",
        "safety": "安全治理",
        "copyright": "版权与合规",
        "benchmark": "评测表现",
        "enterprise": "企业落地",
        "product": "产品化",
    }
    lower = (text or "").lower()
    hits = []
    for k, v in mapping.items():
        if k in lower and v not in hits:
            hits.append(v)
    if not hits:
        return "AI 产品动态"
    return "、".join(hits[:4])


def extract_article_text(page_html):
    if not page_html:
        return ""
    html_text = re.sub(r"<script[\s\S]*?</script>", " ", page_html, flags=re.IGNORECASE)
    html_text = re.sub(r"<style[\s\S]*?</style>", " ", html_text, flags=re.IGNORECASE)

    article_match = re.search(r"<article[\s\S]*?</article>", html_text, flags=re.IGNORECASE)
    if article_match:
        return strip_html(article_match.group(0))

    body_match = re.search(r"<body[\s\S]*?</body>", html_text, flags=re.IGNORECASE)
    if body_match:
        return strip_html(body_match.group(0))

    return strip_html(html_text)


def fetch_article_text(url):
    try:
        return extract_article_text(http_text(url, timeout=25))
    except Exception:
        return ""


def fetch_rss(source_name, rss_url):
    xml_text = http_text(rss_url)
    root = ET.fromstring(xml_text)
    items = []

    rss_items = root.findall(".//item")
    if not rss_items:
        rss_items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    for item in rss_items:
        title = (
            (item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        )
        link = item.findtext("link")
        if link is None:
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            if atom_link is not None:
                link = atom_link.attrib.get("href")
        desc = item.findtext("description") or item.findtext("{http://www.w3.org/2005/Atom}summary") or ""
        published_raw = (
            item.findtext("pubDate")
            or item.findtext("published")
            or item.findtext("updated")
            or item.findtext("{http://www.w3.org/2005/Atom}published")
            or item.findtext("{http://www.w3.org/2005/Atom}updated")
        )
        items.append(
            {
                "title": title,
                "url": (link or "").strip(),
                "description": strip_html(desc),
                "published_at": parse_rss_time(published_raw),
                "source": source_name,
            }
        )
    return items


def fetch_hn():
    query_url = "https://hn.algolia.com/api/v1/search_by_date?query=AI&tags=story&hitsPerPage=50"
    payload = http_json("GET", query_url)
    items = []
    for hit in payload.get("hits", []):
        title = (hit.get("title") or "").strip()
        url = (hit.get("url") or "").strip()
        created_at = hit.get("created_at")
        published_at = None
        if created_at:
            try:
                published_at = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
            except ValueError:
                published_at = None
        if not url:
            object_id = hit.get("objectID")
            if object_id:
                url = f"https://news.ycombinator.com/item?id={object_id}"
        items.append(
            {
                "title": title,
                "url": url,
                "description": "",
                "published_at": published_at,
                "source": "hacker_news",
            }
        )
    return items


def matches_keywords(text, keywords):
    lower = (text or "").lower()
    return any(k.lower() in lower for k in keywords)


def summarize_cn(item):
    title = item.get("title", "")
    desc = item.get("description", "")
    if desc:
        short_desc = desc[:120]
        return f"该资讯聚焦“{title}”，核心内容为：{short_desc}。"
    return f"该资讯聚焦“{title}”，建议查看原文了解完整细节。"


def summarize_detailed_cn(item):
    title = item.get("title", "")
    desc = item.get("description", "")
    article_text = item.get("article_text", "")

    seed = article_text if article_text else desc
    topic_cn = ai_topic_keywords_to_cn(f"{title} {desc}")

    if not seed:
        full = (
            f"详细总结：该新闻围绕“{title}”展开，主题涉及{topic_cn}。"
            "目前公开摘要信息较少，但可以判断其核心仍是 AI 产品能力、应用场景或行业趋势变化。"
            "建议后续持续跟踪官方更新与社区反馈，以获得更完整的事实与影响评估。"
        )
        return full

    if is_mostly_english(seed):
        full = (
            f"详细总结：该新闻围绕“{title}”展开，核心主题为{topic_cn}。"
            "从公开描述看，事件重点涉及 AI 产品在真实场景中的表现与用户预期差异，"
            "同时反映出模型能力边界、交互体验和责任归属等问题。"
            "综合判断，这类信息对产品迭代、风险控制和对外沟通策略具有直接参考意义。"
        )
        return full

    sentences = split_sentences(seed)
    if not sentences:
        return (
            f"详细总结：该新闻围绕“{title}”展开，主题涉及{topic_cn}。"
            "当前可提取的正文信息有限，建议结合原文持续跟进后续细节。"
        )

    core_points = []
    for s in sentences:
        s = s.strip()
        if len(s) < 14:
            continue
        core_points.append(s)
        if len(core_points) >= 4:
            break

    joined = "；".join(core_points)
    if not joined.endswith("。"):
        joined += "。"
    return f"详细总结：{joined}"


def generate_ai_commentary(item):
    text = f"{item.get('title', '')} {item.get('description', '')}"
    topic_cn = ai_topic_keywords_to_cn(text)
    source = item.get("source", "unknown")
    return (
        "AI解读：\n"
        f"行业信号：{topic_cn}依旧处于高热竞争区，头部厂商会持续加速模型能力与产品化节奏。\n"
        "产品机会：可围绕高频真实场景做体验优化与能力打磨，将热点转化为可复用的功能价值。\n"
        "风险点：舆论热度与实际可用性可能不一致，若预期管理不足，容易引发口碑波动与信任损耗。\n"
        f"建议动作：基于{source}这类外部信号建立周度跟踪机制，优先推进稳定性、可解释性与风控策略，并同步优化对外沟通话术。"
    )


def to_local_time_text(utc_time):
    if utc_time is None:
        return "未知时间"
    local_tz = dt.datetime.now().astimezone().tzinfo
    return utc_time.astimezone(local_tz).strftime("%Y-%m-%d %H:%M")


def get_feishu_tenant_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": app_id, "app_secret": app_secret}
    resp = http_json("POST", url, data=data)
    if resp.get("code") != 0:
        raise RuntimeError(f"获取飞书 tenant_access_token 失败: {resp}")
    return resp["tenant_access_token"]


def parse_doc_info(doc_url, headers):
    parsed = urllib.parse.urlparse(doc_url)
    path = parsed.path

    docx_match = re.search(r"/docx/([A-Za-z0-9]+)", path)
    if docx_match:
        return "docx", docx_match.group(1)

    wiki_match = re.search(r"/wiki/([A-Za-z0-9]+)", path)
    if wiki_match:
        wiki_token = wiki_match.group(1)
        wiki_url = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token={wiki_token}"
        node = http_json("GET", wiki_url, headers=headers)
        if node.get("code") != 0:
            raise RuntimeError(f"读取 wiki 节点失败: {node}")
        obj_type = node.get("data", {}).get("node", {}).get("obj_type")
        obj_token = node.get("data", {}).get("node", {}).get("obj_token")
        if obj_type != "docx":
            raise RuntimeError(f"当前 wiki 节点不是 docx，obj_type={obj_type}")
        return "docx", obj_token

    raise RuntimeError("无法从文档链接中识别 docx/wiki token")


def build_feishu_blocks(items):
    now_text = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    blocks = [
        {
            "block_type": 3,
            "heading1": {
                "elements": [
                    {
                        "text_run": {
                            "content": f"AI 热点简报 {now_text}",
                        }
                    }
                ]
            },
        }
    ]

    for idx, item in enumerate(items, start=1):
        line = (
            f"{idx}. {item['title']}\n"
            f"来源：{item['source']} | 时间：{to_local_time_text(item['published_at'])}\n"
            f"{item['full_summary_cn']}\n"
            f"{item['ai_commentary_cn']}\n"
            f"链接：{item['url']}"
        )
        blocks.append(
            {
                "block_type": 2,
                "text": {
                    "elements": [
                        {
                            "text_run": {
                                "content": line,
                            }
                        }
                    ]
                },
            }
        )

    return blocks


def append_to_docx(doc_token, token, blocks):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{doc_token}/children"
    payload = {"children": blocks, "index": -1}
    resp = http_json("POST", url, data=payload, headers=headers)
    if resp.get("code") != 0:
        raise RuntimeError(f"写入飞书文档失败: {resp}")


def collect_items(hours, keywords, limit, summary_depth, fetch_content):
    now_utc = dt.datetime.now(dt.timezone.utc)
    min_time = now_utc - dt.timedelta(hours=hours)
    all_items = []

    for source_name, source_url in DEFAULT_SOURCES.items():
        try:
            all_items.extend(fetch_rss(source_name, source_url))
        except Exception as error:
            print(f"[WARN] RSS 抓取失败 {source_name}: {error}")

    try:
        all_items.extend(fetch_hn())
    except Exception as error:
        print(f"[WARN] HN 抓取失败: {error}")

    filtered = []
    seen = set()
    for item in all_items:
        text = f"{item.get('title', '')} {item.get('description', '')}"
        if not matches_keywords(text, keywords):
            continue
        pub = item.get("published_at")
        if pub is not None and pub < min_time:
            continue
        url = item.get("url", "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        filtered.append(item)

    filtered.sort(key=lambda x: x.get("published_at") or dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc), reverse=True)
    selected = filtered[:limit]

    for item in selected:
        if fetch_content:
            item["article_text"] = fetch_article_text(item.get("url", ""))
        if summary_depth == "detailed":
            item["full_summary_cn"] = summarize_detailed_cn(item)
        else:
            item["full_summary_cn"] = "完整总结：本条为快速模式摘要，建议打开原文查看完整细节。"
        item["ai_commentary_cn"] = generate_ai_commentary(item)
    return selected


def parse_args():
    parser = argparse.ArgumentParser(description="抓取 AI 热点并同步到飞书文档")
    parser.add_argument("--limit", type=int, default=int(os.getenv("HOTSPOT_LIMIT", "10")), help="最多写入条数")
    parser.add_argument("--hours", type=int, default=int(os.getenv("HOTSPOT_HOURS", "24")), help="时间窗口（小时）")
    parser.add_argument("--keywords", type=str, default=os.getenv("HOTSPOT_KEYWORDS", ""), help="逗号分隔关键词")
    parser.add_argument(
        "--summary-depth",
        choices=["simple", "detailed"],
        default=os.getenv("HOTSPOT_SUMMARY_DEPTH", "detailed"),
        help="摘要深度：simple 或 detailed",
    )
    parser.add_argument(
        "--skip-content-fetch",
        action="store_true",
        help="不抓取原文正文（速度更快，摘要较短）",
    )
    return parser.parse_args()


def main():
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(dotenv_path)
    args = parse_args()
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    doc_url = os.getenv("FEISHU_DOC_URL")
    doc_token_env = os.getenv("FEISHU_DOC_TOKEN")

    if not app_id or not app_secret:
        raise RuntimeError("缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
    if not doc_url and not doc_token_env:
        raise RuntimeError("请提供 FEISHU_DOC_URL 或 FEISHU_DOC_TOKEN")

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()] if args.keywords else DEFAULT_KEYWORDS
    items = collect_items(
        hours=args.hours,
        keywords=keywords,
        limit=args.limit,
        summary_depth=args.summary_depth,
        fetch_content=not args.skip_content_fetch,
    )
    if not items:
        print("[INFO] 未抓取到符合条件的 AI 热点")
        return

    tenant_token = get_feishu_tenant_token(app_id, app_secret)
    headers = {"Authorization": f"Bearer {tenant_token}"}

    doc_token = doc_token_env
    if not doc_token:
        obj_type, obj_token = parse_doc_info(doc_url, headers)
        if obj_type != "docx":
            raise RuntimeError("当前仅支持写入 docx 文档")
        doc_token = obj_token

    blocks = build_feishu_blocks(items)
    append_to_docx(doc_token, tenant_token, blocks)

    print(f"[OK] 已写入飞书文档，条数: {len(items)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"[ERROR] {error}")
        sys.exit(1)
