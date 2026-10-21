#!/usr/bin/env python3
"""Build apocalypse12.org, "The Woman & the Dragon" (The Ephesus Challenge).

src/<slug>.html holds each page's <main> content, preceded by a JSON front-matter
line: <!--{"title":..., "description":..., "crumbs":[...], "credit":..., "reviewed":...}-->
Output:
  dist/     production files, clean URLs (/stand-firm), served by .htaccess; published to the main branch
  preview/  same pages with .html links, for previews in an artifact
Adapted from the agreatsign.si build script.
"""
import json, re, shutil, datetime, pathlib, hashlib, math

ROOT = pathlib.Path(__file__).parent
SRC, DIST, PREV = ROOT / "src", ROOT / "dist", ROOT / "preview"
SITE = "https://apocalypse12.org"
SITE_NAME = "The Woman & the Dragon"
# Until launch the site lives at a temporary Hostinger address: no indexing and no redirect to the domain,
# which still serves the old WordPress site. Set to False when apocalypse12.org is pointed here.
PRELAUNCH = True
TODAY = datetime.date.today().isoformat()
# Fr. John's contact address for this site; until it is chosen, pages say it is coming.
CONTACT_EMAIL = "frjohn@apocalypse12.org"
def email_html():
    return (f'<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>' if CONTACT_EMAIL
            else "the contact address on this site's Contact page (coming soon)")
CSS_VERSION = hashlib.md5((ROOT / "assets" / "style.css").read_bytes()).hexdigest()[:8]

# Charter rule 7 (truthful about who did what).
#   default   pages Fr. John wrote with Claude's research and drafting, in his voice
#   "claude"  pages compiled by Claude under his direction (About, How this site is made, the Scorecard)
#   "fr-john" pages he wrote himself
CREDITS = {
    "with": "Written by Fr. John, with research and drafting by Claude, an AI model made by Anthropic.",
    "claude": "Researched and written with Claude, an AI model made by Anthropic. Directed by Fr. John.",
    "fr-john": "Written by Fr. John.",
}
INDEPENDENCE = ("An independent project, part of The Ephesus Challenge. Fr. John is a Catholic diocesan priest, but this "
                "site is his own and is not affiliated with or endorsed by his diocese, the USCCB, Anthropic, or any other "
                "organization.")
FOUNDER = {"@type": "Person", "name": "Fr. John", "url": SITE + "/about", "jobTitle": "Catholic diocesan priest",
           "description": "Founder and author of The Woman & the Dragon"}
SITE_ORG = {"@type": "Organization", "name": SITE_NAME, "url": SITE + "/", "founder": FOUNDER}

def credit_of(meta):
    return CREDITS.get(meta.get("credit", "with"), CREDITS["with"])

# "✓ Reviewed by Fr. John" appears only on pages he has read and approved ("reviewed": "YYYY-MM-DD").
REVIEWED = "✓ Reviewed by Fr. John"

def reviewed_mark(meta, cls="reviewed"):
    d = meta.get("reviewed")
    if not d:
        return ""
    nice = datetime.date.fromisoformat(d).strftime("%B %-d, %Y")
    return f'<span class="{cls}" title="Read and approved by Fr. John on {nice}">{REVIEWED}</span>'

def add_review(body, meta):
    mark = reviewed_mark(meta)
    if not mark:
        return body
    line = f'<p class="review-line">{mark} <a class="review-how" href="/how-this-site-is-made">How this site is made</a></p>'
    if '<p class="crumbs">' in body:
        return re.sub(r'(<p class="crumbs">.*?</p>)', lambda m: m.group(1) + "\n" + line, body, count=1, flags=re.S)
    return re.sub(r'(</section>\s*<div class="wrap[^"]*">)', lambda m: m.group(1) + "\n" + line, body, count=1)

def fix_ld(ld, meta):
    if not isinstance(ld, dict):
        return ld
    ld = dict(ld)
    ld["author"] = SITE_ORG if meta.get("credit") == "claude" else FOUNDER
    ld["creditText"] = credit_of(meta)
    if meta.get("reviewed"):
        ld["reviewedBy"] = FOUNDER
        ld["lastReviewed"] = meta["reviewed"]
    return ld

NAV = [
    ("/", "Home"),
    ("/stand-firm", "Stand Firm"),
    ("/scorecard", "The Evidence"),
    ("/about", "About"),
    ("/contact", "Contact"),
]

def _logo():
    # The Woman clothed with the sun: the sun, a crown of twelve stars, the moon under her feet (Revelation 12:1).
    stars = "".join(
        f'<circle cx="{32 + 20 * math.cos(math.radians(a)):.2f}" cy="{27 + 20 * math.sin(math.radians(a)):.2f}" r="2" fill="#e3c47a"/>'
        for a in range(-90, 270, 30))
    return ('<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="27" r="25" fill="#1c2550"/>' + stars +
            '<circle cx="32" cy="27" r="11" fill="#e3c47a"/><circle cx="32" cy="27" r="7" fill="#f6e3a8"/>'
            '<path d="M13 53 Q32 66 51 53 Q32 59 13 53 Z" fill="#c9a243"/></svg>')
LOGO = _logo()

BOOKS = {"Genesis":"genesis","Exodus":"exodus","Leviticus":"leviticus","Numbers":"numbers","Deuteronomy":"deuteronomy",
"Joshua":"joshua","Judges":"judges","Ruth":"ruth","1 Samuel":"1samuel","2 Samuel":"2samuel","1 Kings":"1kings","2 Kings":"2kings",
"1 Chronicles":"1chronicles","2 Chronicles":"2chronicles","Ezra":"ezra","Nehemiah":"nehemiah","Tobit":"tobit","Judith":"judith",
"Esther":"esther","1 Maccabees":"1maccabees","2 Maccabees":"2maccabees","Job":"job","Psalms":"psalms","Psalm":"psalms",
"Proverbs":"proverbs","Ecclesiastes":"ecclesiastes","Song of Songs":"songofsongs","Wisdom":"wisdom","Sirach":"sirach",
"Isaiah":"isaiah","Jeremiah":"jeremiah","Lamentations":"lamentations","Baruch":"baruch","Ezekiel":"ezekiel","Daniel":"daniel",
"Hosea":"hosea","Joel":"joel","Amos":"amos","Obadiah":"obadiah","Jonah":"jonah","Micah":"micah","Nahum":"nahum",
"Habakkuk":"habakkuk","Zephaniah":"zephaniah","Haggai":"haggai","Zechariah":"zechariah","Malachi":"malachi",
"Matthew":"matthew","Mark":"mark","Luke":"luke","John":"john","Acts":"acts","Romans":"romans","1 Corinthians":"1corinthians",
"2 Corinthians":"2corinthians","Galatians":"galatians","Ephesians":"ephesians","Philippians":"philippians","Colossians":"colossians",
"1 Thessalonians":"1thessalonians","2 Thessalonians":"2thessalonians","1 Timothy":"1timothy","2 Timothy":"2timothy","Titus":"titus",
"Philemon":"philemon","Hebrews":"hebrews","James":"james","1 Peter":"1peter","2 Peter":"2peter","1 John":"1john","2 John":"2john",
"3 John":"3john","Jude":"jude","Revelation":"revelation",
"Gen":"genesis","Deut":"deuteronomy","Dan":"daniel","Matt":"matthew","Rev":"revelation","Rom":"romans","Thess":"2thessalonians"}
BOOKS.pop("Thess")
_names = sorted(BOOKS, key=len, reverse=True)
REF = re.compile(r"(?<![\w])(" + "|".join(re.escape(n) for n in _names) + r")\s(\d{1,3})(?:[:.](\d{1,3}[a-z]{0,2}(?:[–-]\d{1,3}[a-z]{0,2})?))?(?:[–-]\d{1,3}(?::\d{1,3})?)?(?!\w|:\d)")
REF_ABBR = re.compile(r"(?<![\w])(1|2) Thess\s(\d{1,2})(?::(\d{1,2}(?:[–-]\d{1,2})?))?")
SKIP = {"a", "h1", "h2", "h3", "title", "script", "style", "head", "button"}

def _walk(html, fn):
    out, depth = [], 0
    for part in re.split(r"(<[^>]+>)", html):
        if part.startswith("<"):
            m = re.match(r"<(/?)([a-zA-Z0-9]+)", part)
            if m and m.group(2).lower() in SKIP and not part.endswith("/>"):
                depth += -1 if m.group(1) else 1
            out.append(part)
        elif depth > 0 or not part.strip():
            out.append(part)
        else:
            out.append(fn(part))
    return "".join(out)

def _sref(slug, ch, text):
    return f'<a class="sref" href="https://bible.usccb.org/bible/{slug}/{ch}" target="_blank" rel="noopener">{text}</a>'

def link_scripture(html):
    def fn(part):
        part = REF_ABBR.sub(lambda m: _sref(f"{m.group(1)}thessalonians", m.group(2), m.group(0)), part)
        # skip text already turned into a link above
        pieces = re.split(r"(<a [^>]+>.*?</a>)", part)
        return "".join(p if p.startswith("<a ") else REF.sub(lambda m: _sref(BOOKS[m.group(1)], m.group(2), m.group(0)), p)
                       for p in pieces)
    return _walk(html, fn)

# Catechism of the Catholic Church: paragraph -> IntraText page on vatican.va (ccc_pages.json, from agreatsign.si).
_CCC = json.load(open(ROOT / "ccc_pages.json"))
def ccc_page(n):
    for a, z, pid in _CCC:
        if a <= n <= z:
            return f"https://www.vatican.va/archive/ENG0015/__P{pid}.HTM"
    return None
CCC_REF = re.compile(r"\b(CCC|Catechism)(\s|&nbsp;)(\d{1,4}(?:[–-]\d{1,4})?(?:,\s?\d{1,4}(?:[–-]\d{1,4})?)*)")
def _ccc_num(numtext):
    n = int(re.match(r"\d+", numtext).group(0))
    url = ccc_page(n) if 1 <= n <= 2865 else None
    return f'<a class="cref" href="{url}" target="_blank" rel="noopener">{numtext}</a>' if url else numtext
def _ccc_rep(m):
    word, sp, nums = m.group(1), m.group(2), m.group(3)
    parts = re.split(r"(,\s?)", nums)
    n = int(re.match(r"\d+", parts[0]).group(0))
    url = ccc_page(n) if 1 <= n <= 2865 else None
    head = f'<a class="cref" href="{url}" target="_blank" rel="noopener">{word}{sp}{parts[0]}</a>' if url else f"{word}{sp}{parts[0]}"
    return head + "".join(p if p.startswith(",") else _ccc_num(p) for p in parts[1:])
def link_catechism(html):
    return _walk(html, lambda part: CCC_REF.sub(_ccc_rep, part))

def page(slug, meta, body):
    path = "/" if slug == "index" else f"/{slug}"
    nav = "".join(f'<li><a href="{h}"{" aria-current=page" if h == path else ""}>{t}</a></li>' for h, t in NAV)
    crumbs = ""
    if meta.get("crumbs"):
        items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u}
                 for i, (n, u) in enumerate(meta["crumbs"])]
        crumbs = ('<script type="application/ld+json">' +
                  json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}) + "</script>")
    ld = fix_ld(meta.get("ld", ""), meta)
    ld = ('<script type="application/ld+json">' + json.dumps(ld) + "</script>") if ld else ""
    title = meta["title"]
    robots = '<meta name="robots" content="noindex">\n' if PRELAUNCH else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta['description']}">
{robots}<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="{'website' if slug == 'index' else 'article'}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta['description']}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:locale" content="en_US">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Inter:wght@400;600;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={CSS_VERSION}">
{crumbs}{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap">
<a class="brand" href="/">{LOGO}<span>The Woman &amp; the Dragon</span></a>
<button class="nav-toggle" aria-expanded="false" aria-controls="nav">Menu</button>
<nav class="nav" id="nav" aria-label="Main"><ul>{nav}</ul></nav>
</div></header>
<main id="main">
{body}
</main>
<footer class="site-foot"><div class="wrap">
<div class="cols">
<div><h4>The Woman &amp; the Dragon</h4><p>Fr. John's reading of Revelation 12 and 13: a possibility tested by the marks of Scripture, and help to stand firm, with Mary and the saints, in a time of trial.</p></div>
<div><h4>Explore</h4><ul>{''.join(f'<li><a href="{h}">{t}</a></li>' for h, t in NAV[1:])}<li><a href="/how-this-site-is-made">How This Site Is Made</a></li></ul></div>
<div><h4>The Ephesus Challenge</h4><ul><li><a href="https://thelambsvictory.org/" target="_blank" rel="noopener">The Lamb's Victory</a>: Revelation chapter by chapter</li><li><a href="https://agreatsign.si/" target="_blank" rel="noopener">A Great Sign</a>: prophecy across the whole Bible</li></ul></div>
</div>
<p class="credit">{credit_of(meta)}{(" " + reviewed_mark(meta)) if meta.get("reviewed") else ""} <a href="/how-this-site-is-made">How this site is made</a></p>
<p class="fine">{INDEPENDENCE}</p>
<p class="fine">© {datetime.date.today().year} Fr. John · Scripture quotations are from the New American Bible, Revised Edition © 2010, 1991, 1986, 1970 Confraternity of Christian Doctrine, Washington, D.C., used by permission. All rights reserved.</p>
</div></footer>
<script>
document.querySelector('.nav-toggle').addEventListener('click',function(){{var n=document.getElementById('nav');var o=n.classList.toggle('open');this.setAttribute('aria-expanded',o)}});
</script>
</body>
</html>
"""

def to_preview(html):
    def fix(m):
        attr, url = m.group(1), m.group(2)
        if url == "/":
            return f'{attr}="index.html"'
        if url.startswith("/assets/"):
            return f'{attr}="{url[1:]}"'
        frag = ""
        if "#" in url:
            url, frag = url.split("#", 1); frag = "#" + frag
        return f'{attr}="{url[1:]}.html{frag}"'
    return re.sub(r'(href|src)="(/[^"/][^"]*|/)"', fix, html)

HTACCESS_REDIRECT = """# https and no www
RewriteCond %{HTTPS} off [OR]
RewriteCond %{HTTP_HOST} ^www\\. [NC]
RewriteRule ^ https://apocalypse12.org%{REQUEST_URI} [L,R=301]
"""
HTACCESS = """Options -Indexes
DirectoryIndex index.html
ErrorDocument 404 /404.html
RewriteEngine On
@REDIRECT@# /page.html -> /page
RewriteCond %{THE_REQUEST} \\s/+(.+?)\\.html[\\s?] [NC]
RewriteRule ^ /%1 [L,R=301]
# /page -> page.html
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME}.html -f
RewriteRule ^(.+?)/?$ $1.html [L]
<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType text/css "access plus 1 week"
ExpiresByType image/svg+xml "access plus 1 month"
</IfModule>
"""

def main():
    for d in (DIST, PREV):
        if d.exists():
            shutil.rmtree(d)
        (d / "assets").mkdir(parents=True)
        for f in (ROOT / "assets").iterdir():
            shutil.copy(f, d / "assets" / f.name)
        (d / "assets" / "favicon.svg").write_text(LOGO.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" '))
    urls = []
    for f in sorted(SRC.glob("*.html")):
        text = f.read_text()
        m = re.match(r"<!--(\{.*?\})-->\n", text, re.S)
        meta, body = json.loads(m.group(1)), text[m.end():]
        body = add_review(link_catechism(link_scripture(body.replace("<!--EMAIL-->", email_html()))), meta)
        html = page(f.stem, meta, body)
        (DIST / f"{f.stem}.html").write_text(html)
        (PREV / f"{f.stem}.html").write_text(to_preview(html))
        if f.stem != "404":
            urls.append("/" if f.stem == "index" else f"/{f.stem}")
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n" if PRELAUNCH
                                     else f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    (DIST / ".htaccess").write_text(HTACCESS.replace("@REDIRECT@", "" if PRELAUNCH else HTACCESS_REDIRECT))
    print("built", len(urls), "pages:", ", ".join(urls))

if __name__ == "__main__":
    main()
