import json
import os
import subprocess
import urllib.error
import urllib.request


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


def http_json(method, url, headers=None, data=None, timeout=20):
    headers = headers or {}
    body = None
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json; charset=utf-8"}
    req = urllib.request.Request(url=url, method=method, headers=headers, data=body)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {error.code} | {body}") from error


def get_tenant_token(app_id, app_secret):
    resp = http_json(
        "POST",
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data={"app_id": app_id, "app_secret": app_secret},
    )
    return resp.get("tenant_access_token", "")


def collect_jobs_text():
    cmd = [
        "python",
        ".opencode/skills/teacher-jobs-to-feishu/scripts/sync_teacher_jobs_to_feishu.py",
        "--max-items",
        "200",
        "--lookback-days",
        "120",
        "--detail-fetch-limit",
        "300",
        "--table-score-threshold",
        "4",
        "--debug-stats",
        "--dry-run",
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="ignore")
    lines = [x.strip() for x in out.splitlines() if x.strip().startswith("[DRY_RUN] #")]
    if not lines:
        return "生物岗位同步测试（近4个月）\n未提取到岗位行"
    return "生物岗位同步测试（近4个月）\n" + "\n".join(lines[:7])


def pick_target_chat(headers):
    resp = http_json("GET", "https://open.feishu.cn/open-apis/im/v1/chats?page_size=50", headers=headers)
    items = resp.get("data", {}).get("items", [])
    if not items:
        return None
    for chat in items:
        if "效率极客" in (chat.get("name") or ""):
            return chat
    return items[0]


def send_message(headers, chat_id, text):
    return http_json(
        "POST",
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers=headers,
        data={
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        },
    )


def main():
    load_dotenv(".opencode/skills/teacher-jobs-to-feishu/.env")
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        print("[ERROR] 缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
        return

    text = collect_jobs_text()
    token = get_tenant_token(app_id, app_secret)
    if not token:
        print("[ERROR] 获取 tenant_access_token 失败")
        return

    headers = {"Authorization": f"Bearer {token}"}
    chat = pick_target_chat(headers)
    if not chat:
        print("[ERROR] 当前应用未发现可发送的群（im/v1/chats 为空）")
        return

    chat_id = chat.get("chat_id")
    chat_name = chat.get("name")
    try:
        resp = send_message(headers, chat_id, text)
        print(f"[OK] 已发送到群: {chat_name} | code={resp.get('code')} msg={resp.get('msg')}")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")
        print(f"[ERROR] 发送失败 HTTP {error.code} | {body}")


if __name__ == "__main__":
    main()
