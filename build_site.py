# 把理论包 Markdown 生成为单页静态网站。
import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / "方法理论包_Markov与Lancet健康收益.md"
FIG = ROOT.parent / "figures"
OUT_FIG = ROOT / "figures"


def inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def slug(title, used):
    base = re.sub(r"\s+", "-", title.strip())
    base = re.sub(r"[^\w\u4e00-\u9fff.\-]+", "", base)
    base = base.strip("-") or "section"
    n = used.get(base, 0)
    used[base] = n + 1
    return base if n == 0 else f"{base}-{n}"


def render(md):
    lines = md.splitlines()
    body = []
    toc = []
    used = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            body.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*-+", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            head, data = rows[0], rows[2:]
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            trs = []
            for row in data:
                trs.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            body.append("<div class='table-wrap'><table><thead><tr>" + th + "</tr></thead><tbody>" + "".join(trs) + "</tbody></table></div>")
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            sid = slug(title, used)
            toc.append((level, sid, title))
            body.append(f"<h{level} id='{sid}'>{inline(title)}</h{level}>")
            i += 1
            continue
        img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line.strip())
        if img:
            alt, src = img.group(1), img.group(2)
            body.append(f"<figure><img src='{html.escape(src)}' alt='{html.escape(alt)}'><figcaption>{inline(alt)}</figcaption></figure>")
            i += 1
            continue
        if re.match(r"^[-*] ", line):
            items = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i]):
                items.append("<li>" + inline(lines[i][2:].strip()) + "</li>")
                i += 1
            body.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\. ", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append("<li>" + inline(re.sub(r"^\d+\. ", "", lines[i]).strip()) + "</li>")
                i += 1
            body.append("<ol>" + "".join(items) + "</ol>")
            continue
        if not line.strip():
            i += 1
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,3}\s|```|\||!\[|[-*] |\d+\. )", lines[i]):
            para.append(lines[i].strip())
            i += 1
        body.append("<p>" + inline(" ".join(para)) + "</p>")
    return toc, "\n".join(body)


def toc_html(toc):
    parts = ["<nav class='toc'><p class='toc-title'>目录</p>"]
    for level, sid, title in toc:
        if level == 1:
            continue
        parts.append(f"<a class='lv{level}' href='#{sid}'>{html.escape(title)}</a>")
    parts.append("</nav>")
    return "\n".join(parts)


PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>答辩方法理论包：Markov 与 Lancet 健康收益</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<header class="top">
  <div>
    <p class="kicker">毕业答辩备读</p>
    <strong>Markov 与 Lancet 健康收益</strong>
  </div>
  <a class="src" href="方法理论包_Markov与Lancet健康收益.md">Markdown 原文</a>
</header>
<div class="layout">
{toc}
<main>
{body}
</main>
</div>
</body>
</html>
"""


def main():
    if OUT_FIG.exists():
        shutil.rmtree(OUT_FIG)
    OUT_FIG.mkdir(parents=True)
    for png in FIG.glob("*.png"):
        shutil.copy2(png, OUT_FIG / png.name)
    md = SRC.read_text(encoding="utf-8")
    shutil.copy2(SRC, ROOT / SRC.name)
    toc, body = render(md)
    html_out = PAGE.format(toc=toc_html(toc), body=body)
    (ROOT / "index.html").write_text(html_out, encoding="utf-8")
    print("sections", len(toc), "bytes", len(html_out))


if __name__ == "__main__":
    main()
