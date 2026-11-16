"""Build a single self-contained HTML file with every photo embedded once.

Usage:  python3 build.py
Output: ../Tanbaly-3D.html  (one file: open it anywhere, share it, upload it)
"""
import base64, json, os, re, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "index.html")
OUT = os.path.join(HERE, "..", "Tanbaly-3D.html")

html = open(SRC, encoding="utf-8").read()
names = sorted(set(re.findall(r"img/[a-z0-9-]+\.jpg", html)))

def data_uri(rel):
    with tempfile.TemporaryDirectory() as tmp:
        small = os.path.join(tmp, "x.jpg")
        # shrink to max 1400px and recompress so the single file stays light
        subprocess.run(["sips", "-Z", "1400", "-s", "formatOptions", "70", os.path.join(HERE, rel), "--out", small],
                       check=True, capture_output=True)
        return "data:image/jpeg;base64," + base64.b64encode(open(small, "rb").read()).decode()

imgs = {n: data_uri(n) for n in names}
var = lambda n: "--" + n.replace("/", "-").replace(".jpg", "")

# CSS / inline-style backgrounds -> CSS variables
html = re.sub(r"url\((img/[a-z0-9-]+\.jpg)\)", lambda m: f"var({var(m.group(1))})", html)
# <img src="img/..."> -> data-img, filled by a tiny script
html = re.sub(r'src="(img/[a-z0-9-]+\.jpg)"', r'data-img="\1"', html)
# JS string literals -> lookup
html = re.sub(r"'(img/[a-z0-9-]+\.jpg)'", r"IMGS['\1']", html)

head = ("<script>window.IMGS=" + json.dumps(imgs) + ";"
        "for(const k in IMGS)document.documentElement.style.setProperty('--'+k.replace('/','-').replace('.jpg',''),'url('+IMGS[k]+')');"
        "</script>\n")
fill = "<script>document.querySelectorAll('[data-img]').forEach(e=>e.src=IMGS[e.dataset.img]);</script>\n"
html = html.replace("</head>", head + "</head>", 1)
html = html.replace('<script type="importmap">', fill + '<script type="importmap">', 1)

leftover = re.findall(r"img/[a-z0-9-]+\.jpg", re.sub(r"IMGS\['img/[^']+'\]|data-img=\"img/[^\"]+\"|\"img/[a-z0-9-]+\.jpg\":", "", html))
open(OUT, "w", encoding="utf-8").write(html)
print(f"{len(imgs)} images embedded -> {os.path.normpath(OUT)} ({os.path.getsize(OUT)/1e6:.1f} MB); unresolved refs: {leftover}")
