"""はてなブログのフィードから最新記事を取得し、index.html の最新記事リンクを更新する。"""
import html
import re
import urllib.request
import xml.etree.ElementTree as ET

FEED = "https://hanabibanban.hatenablog.com/feed"
COUNT = 3  # 表示する記事数
NS = {"a": "http://www.w3.org/2005/Atom"}

req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0 (link-page updater)"})
root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())

items = []
for e in root.findall("a:entry", NS)[:COUNT]:
    title = (e.findtext("a:title", "", NS) or "").strip()
    link = next((l.get("href") for l in e.findall("a:link", NS) if l.get("rel", "alternate") == "alternate"), "")
    summary = re.sub(r"\s+", " ", e.findtext("a:summary", "", NS) or "").strip()
    # 冒頭の「※この記事にはプロモーション（広告）が含まれています。」などの注記を飛ばす
    summary = re.sub(r"^(?:※[^。]*。\s*)+", "", summary)
    if len(summary) > 24:
        summary = summary[:24] + "…"
    items.append(
        f'    <a class="btn" href="{html.escape(link)}"><span class="em">🆕</span>'
        f'<span class="t"><b>{html.escape(title)}</b><small>{html.escape(summary)}</small></span></a>'
    )

if not items:
    raise SystemExit("フィードに記事がありません")

path = "index.html"
src = open(path, encoding="utf-8").read()
block = "<!-- latest:start -->\n" + "\n".join(items) + "\n    <!-- latest:end -->"
out, n = re.subn(r"<!-- latest:start -->.*?<!-- latest:end -->", lambda m: block, src, flags=re.S)
if n != 1:
    raise SystemExit("index.html にマーカーが見つかりません")
open(path, "w", encoding="utf-8").write(out)
