"""
模板過濾器
- render_content：內文自動嵌入圖片與 YouTube（對應 Bad UI 問題 6：多媒體預覽）
- highlight：搜尋結果關鍵字標示
"""
import re
from urllib.parse import parse_qs, urlparse

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

URL_RE = re.compile(r"(https?://[^\s<>\"']+)")
IMG_RE = re.compile(r"\.(jpe?g|png|gif|webp)(\?.*)?$", re.I)


def _youtube_id(url):
    u = urlparse(url)
    host = u.netloc.lower().replace("www.", "").replace("m.", "")
    if host == "youtu.be":
        return u.path.lstrip("/").split("/")[0] or None
    if host == "youtube.com":
        if u.path == "/watch":
            return parse_qs(u.query).get("v", [None])[0]
        if u.path.startswith(("/shorts/", "/embed/")):
            return u.path.split("/")[2]
    return None


def _render_url(match):
    url = match.group(1)
    yt = _youtube_id(url)
    if yt and re.fullmatch(r"[\w-]{6,20}", yt):
        return (f'<div class="embed-video"><iframe src="https://www.youtube.com/embed/{yt}" '
                f'title="YouTube 影片" loading="lazy" allowfullscreen></iframe></div>')
    if IMG_RE.search(url):
        return f'<a href="{url}" target="_blank" rel="noopener"><img class="embed-img" src="{url}" alt="文章圖片" loading="lazy"></a>'
    return f'<a href="{url}" target="_blank" rel="noopener nofollow">{url}</a>'


@register.filter
def render_content(text):
    safe = escape(text or "")
    paragraphs = []
    for block in re.split(r"\n\s*\n", safe.strip()):
        html = URL_RE.sub(_render_url, block).replace("\n", "<br>")
        paragraphs.append(f"<p>{html}</p>")
    return mark_safe("\n".join(paragraphs))


@register.filter
def highlight(text, q):
    safe = escape(text or "")
    if not q:
        return mark_safe(safe)
    pattern = re.compile(re.escape(escape(q)), re.I)
    return mark_safe(pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", safe))


@register.filter
def excerpt(text, length=80):
    plain = URL_RE.sub("", text or "").replace("\n", " ").strip()
    return plain[:length] + ("…" if len(plain) > length else "")


@register.simple_tag(takes_context=True)
def qs(context, **kwargs):
    """保留目前查詢參數並覆寫部分參數，用在分頁與篩選連結"""
    params = context["request"].GET.copy()
    for k, v in kwargs.items():
        if v in (None, ""):
            params.pop(k, None)
        else:
            params[k] = v
    if "page" not in kwargs:
        params.pop("page", None)
    return "?" + params.urlencode()
