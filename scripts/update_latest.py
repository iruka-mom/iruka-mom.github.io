"""はてなブログのフィードから最新記事とカテゴリを取得し、index.html を更新する。"""
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BLOG = "https://hanabibanban.hatenablog.com"
FEED = BLOG + "/feed"
COUNT = 3  # 表示する記事数
NS = {"a": "http://www.w3.org/2005/Atom"}

req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0 (link-page updater)"})
root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
entries = root.findall("a:entry", NS)

# ---- 最新記事 ----
items = []
for e in entries[:COUNT]:
    title = (e.findtext("a:title", "", NS) or "").strip()
    link = next((l.get("href") for l in e.findall("a:link", NS) if l.get("rel", "alternate") == "alternate"), "")
    published = (e.findtext("a:published", "", NS) or e.findtext("a:updated", "", NS) or "").strip()
    summary = re.sub(r"\s+", " ", e.findtext("a:summary", "", NS) or "").strip()
    # 冒頭の「※この記事にはプロモーション（広告）が含まれています。」などの注記を飛ばす
    summary = re.sub(r"^(?:※[^。]*。\s*)+", "", summary)
    if len(summary) > 24:
        summary = summary[:24] + "…"
    items.append(
        f'    <a class="btn" href="{html.escape(link)}" data-published="{html.escape(published)}">'
        f'<span class="t"><b>{html.escape(title)}</b><small>{html.escape(summary)}</small></span></a>'
    )

if not items:
    raise SystemExit("フィードに記事がありません")

path = "index.html"
src = open(path, encoding="utf-8").read()


def replace_block(text, name, body):
    pattern = rf"<!-- {name}:start -->.*?<!-- {name}:end -->"
    out, n = re.subn(pattern, lambda m: f"<!-- {name}:start -->\n{body}  <!-- {name}:end -->", text, flags=re.S)
    if n != 1:
        raise SystemExit(f"index.html に {name} のマーカーが見つかりません")
    return out


src = replace_block(src, "latest", "\n".join(items) + "\n  ")

# ---- カテゴリ ----
# フィードには最近の記事しか載らないので、これまでに見つけたカテゴリは残して新しいものを足していく
cats = re.findall(r'data-cat="([^"]*)"', re.search(r"<!-- cats:start -->.*?<!-- cats:end -->", src, re.S).group(0))
cats = [html.unescape(c) for c in cats]
for e in entries:
    for c in e.findall("a:category", NS):
        term = (c.get("term") or "").strip()
        if term and term not in cats:
            cats.append(term)

if cats:
    buttons = "\n".join(
        f'    <a href="{BLOG}/archive/category/{urllib.parse.quote(c)}" data-cat="{html.escape(c)}">{html.escape(c)}</a>'
        for c in cats
    )
    body = f'  <h2>カテゴリで探す</h2>\n  <div class="cats">\n{buttons}\n  </div>\n'
else:
    body = ""
src = replace_block(src, "cats", body)

open(path, "w", encoding="utf-8").write(src)
