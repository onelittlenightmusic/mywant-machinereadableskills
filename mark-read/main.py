#!/usr/bin/env python3
"""
mark-read: list-unread-gmail で表示した番号のメールを既読にする。
list-unread-gmail が保存したキャッシュ /tmp/gmail_unread_list.json を参照する。

出力形式 (JSON):
{
  "marked_no": 3,
  "subject": "件名",
  "sender": "送信者名",
  "date": "4月11日"
}
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

CDP_URL = "http://127.0.0.1:9222"
CACHE_FILE = "/tmp/gmail_unread_list.json"


def error_out(message: str) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False))
    sys.exit(1)


def load_cache() -> list[dict]:
    p = Path(CACHE_FILE)
    if not p.exists():
        error_out("メールリストが見つかりません。先に list-unread-gmail を実行してください。")
    return json.loads(p.read_text(encoding="utf-8"))


def mark_email_read(page, email: dict) -> None:
    subject = email["subject"]
    thread_id = email.get("thread_id", "")

    page.goto("https://mail.google.com/mail/u/0/#imp", wait_until="domcontentloaded", timeout=15000)

    try:
        page.wait_for_selector("div[role='main']", timeout=10000)
    except PlaywrightTimeout:
        error_out("Gmailの読み込みがタイムアウトしました。")

    clicked = False

    if thread_id:
        row = page.query_selector(f"tr[data-thread-id='{thread_id}']")
        if row:
            row.click()
            clicked = True

    if not clicked:
        for row in page.query_selector_all("tr.zE"):
            subj_el = row.query_selector("span.bqe, span.bog")
            if subj_el and subject in subj_el.inner_text():
                row.click()
                clicked = True
                break

    if not clicked:
        error_out(f"メール「{subject}」が見つかりませんでした。既読済みの可能性があります。")

    try:
        page.wait_for_selector("div.a3s", timeout=8000)
    except PlaywrightTimeout:
        pass  # 開けていれば既読になっている


def main() -> None:
    if len(sys.argv) < 2:
        error_out("使い方: python3 main.py <番号>  例: python3 main.py 3")

    try:
        no = int(sys.argv[1])
    except ValueError:
        error_out(f"番号を整数で指定してください (指定値: {sys.argv[1]})")

    emails = load_cache()
    target = next((e for e in emails if e["no"] == no), None)
    if target is None:
        valid = [e["no"] for e in emails]
        error_out(f"番号 {no} のメールが見つかりません。有効な番号: {valid}")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            error_out(f"ブラウザに接続できません ({CDP_URL}): {e}")

        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()

        mark_email_read(page, target)

    print(json.dumps({
        "marked_no": target["no"],
        "subject": target["subject"],
        "sender": target["sender"],
        "date": target["date"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
