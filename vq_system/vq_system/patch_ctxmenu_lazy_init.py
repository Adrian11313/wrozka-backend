from pathlib import Path
from datetime import datetime
import re

path = Path("app/web/templates/vq_matrix.html")
src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_ctxlazy_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

# 1) Zamie stae pobranie ctxMenu/ctxTitle/ctxItems na lazy-init
# Szukamy bloku:
# var ctxMenu = document.getElementById("ctxMenu");
# var ctxTitle = document.getElementById("ctxTitle");
# var ctxItems = document.getElementById("ctxItems");
pat = re.compile(
    r'var\s+ctxMenu\s*=\s*document\.getElementById\(["\']ctxMenu["\']\);\s*'
    r'var\s+ctxTitle\s*=\s*document\.getElementById\(["\']ctxTitle["\']\);\s*'
    r'var\s+ctxItems\s*=\s*document\.getElementById\(["\']ctxItems["\']\);\s*',
    re.M
)

replacement = r'''
  // ctxMenu is rendered AFTER <script>, so we must get elements lazily
  var ctxMenu = null;
  var ctxTitle = null;
  var ctxItems = null;

  function ensureCtxEls() {
    if (!ctxMenu) ctxMenu = document.getElementById("ctxMenu");
    if (!ctxTitle) ctxTitle = document.getElementById("ctxTitle");
    if (!ctxItems) ctxItems = document.getElementById("ctxItems");
    return !!(ctxMenu && ctxTitle && ctxItems);
  }
'''

if pat.search(src):
    src = pat.sub(replacement, src, count=1)
    print("OK: podmieniono ctxMenu init na lazy.")
else:
    # jeli nie znalelimy dokadnego bloku, spróbujmy prostszej wersji:
    if 'getElementById("ctxMenu")' in src or "getElementById('ctxMenu')" in src:
        print("UWAGA: nie znalazem dokadnego bloku 3 linii. Wklej fragment JS z ctxMenu jeli nadal nie dziaa.")
    else:
        print("UWAGA: w pliku nie widz w ogóle ctxMenu JS. Jeli menu nie istnieje, trzeba go doda.")

# 2) W openContextMenu dodaj ensureCtxEls() na pocztku (jeli nie ma)
# Szukamy: function openContextMenu(cell, x, y) {
open_pat = re.compile(r'function\s+openContextMenu\s*\(\s*cell\s*,\s*x\s*,\s*y\s*\)\s*\{\s*', re.M)

def add_ensure(m):
    return m.group(0) + '\n    if (!ensureCtxEls()) return;\n'

# dodajemy tylko jeli ensureCtxEls jest zdefiniowane i nie ma go ju w openContextMenu
if "function ensureCtxEls()" in src:
    # jeli openContextMenu ju ma ensureCtxEls -> nie duplikuj
    if re.search(r'function\s+openContextMenu[\s\S]*?ensureCtxEls\(\)', src):
        print("OK: openContextMenu ju ma ensureCtxEls().")
    else:
        src, n = open_pat.subn(add_ensure, src, count=1)
        print("OK: dodano ensureCtxEls() w openContextMenu." if n else "UWAGA: nie znalazem openContextMenu().")
else:
    print("UWAGA: brak ensureCtxEls(), wic nie dodaj do openContextMenu.")

path.write_text(src, encoding="utf-8")
print("Zapisano:", path)
print("DONE")
