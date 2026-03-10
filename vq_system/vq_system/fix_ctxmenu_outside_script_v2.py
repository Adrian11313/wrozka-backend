import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono pliku: {path}")

src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_fix2_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) Wytnij wszystkie bloki Context Menu (eby nie byo duplikatów i eby nie siedziay w <script>)
menu_pat = re.compile(
    r"\s*<!-- Context Menu \(prawy klik\) -->\s*\n"
    r"\s*<div id=\"ctxMenu\".*?</div>\s*\n",
    re.DOTALL
)

menus = menu_pat.findall(out)
out = menu_pat.sub("\n", out)
print("Usunite bloki ctxMenu:", len(menus))

# 2) Jeli nie byo adnego bloku, to dodaj standardowy
if menus:
    menu_block = menus[0]
else:
    menu_block = """
<!-- Context Menu (prawy klik) -->
<div id="ctxMenu" style="position:fixed; display:none; background:#111; color:#fff; border-radius:10px; padding:8px; z-index:9999; width:280px; box-shadow:0 10px 30px rgba(0,0,0,0.25);">
  <div id="ctxTitle" style="font-weight:600; margin-bottom:6px;">Opcje</div>
  <div id="ctxItems"></div>
</div>
"""

# 3) Wstaw blok przed </body> (najbezpieczniej)
pos_body = out.lower().rfind("</body>")
if pos_body == -1:
    raise SystemExit("Nie znalazem </body> w vq_matrix.html")

out = out[:pos_body] + "\n" + menu_block.strip() + "\n" + out[pos_body:]

# 4) Prosty test: ctxMenu nie moe by midzy <script> a </script>
# (sprawdzamy, czy wystpuje w jakimkolwiek segmencie <script>...</script>)
bad = False
for m in re.finditer(r"<script[^>]*>(.*?)</script>", out, re.DOTALL | re.IGNORECASE):
    if "id=\"ctxMenu\"" in m.group(1) or "Context Menu (prawy klik)" in m.group(1):
        bad = True
        break

if bad:
    raise SystemExit("ctxMenu nadal siedzi w <script>. Podelij kocówk pliku vq_matrix.html (ostatnie ~120 linii).")

path.write_text(out, encoding="utf-8")
print("OK: ctxMenu jest poza <script> i przed </body>.")
print("Zapisano:", path)
