"""Streamlit Community Cloudのアプリを開き、休止中なら起動ボタンを押す。"""
import os
import re
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = os.environ["APP_URL"]
WAKE_TEXT = re.compile(r"get this app back up", re.I)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(10_000)

    button = page.get_by_role("button", name=WAKE_TEXT)
    if button.count() > 0:
        print("休止中でした。起動ボタンを押します。")
        button.first.click()
        try:
            button.first.wait_for(state="detached", timeout=180_000)
            print("起動しました。")
        except PWTimeout:
            print("起動ボタンが消えませんでした。手動で確認してください。")
            browser.close()
            sys.exit(1)
    else:
        print("起動中でした（アクセスで休止タイマーもリセット）。")

    # しばらく開いたままにして、アクセスとして確実に記録させる
    page.wait_for_timeout(20_000)
    browser.close()
