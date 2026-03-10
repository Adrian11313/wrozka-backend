from pathlib import Path
from datetime import datetime
import re

path = Path("app/web/templates/vq_matrix.html")
src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_ctx_vs_tip_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) Dodaj flag ctxOpen przy tipCache (eby blokowa hover gdy menu otwarte)
if "var ctxOpen" not in out:
    out, n = re.subn(
        r"(var\s+tipCache\s*=\s*\{\}\s*;[^\n]*\n)",
        r"\1  var ctxOpen = false; // when context menu is open, disable tooltip hover\n",
        out,
        count=1
    )
    if n:
        print("OK: dodano ctxOpen przy tipCache.")
    else:
        print("UWAGA: nie znalazem 'var tipCache = {}'. Spróbuj doda ctxOpen globalnie.")
        # fallback - wrzu gdziekolwiek na pocztku IIFE
        out, n2 = re.subn(r"\(function\(\)\{\s*", "(function(){\n  var ctxOpen = false; // when context menu is open, disable tooltip hover\n", out, count=1)
        print("OK: dodano ctxOpen na pocztku IIFE." if n2 else "UWAGA: nie udao si doda ctxOpen.")

# 2) Zablokuj loadHistory gdy ctxOpen == true
if "if (ctxOpen) return;" not in out:
    out, n = re.subn(
        r"(function\s+loadHistory\s*\(\s*cell\s*\)\s*\{\s*)",
        r"\1\n    if (typeof ctxOpen !== 'undefined' && ctxOpen) return;\n",
        out,
        count=1
    )
    print("OK: loadHistory blokuje si gdy menu otwarte." if n else "UWAGA: nie znalazem function loadHistory(cell).")

# 3) W oncontextmenu: ukryj tooltip + ustaw ctxOpen=true
# Szukamy: cell.oncontextmenu = function(e){ ... openContextMenu(...)
pat_ctx = re.compile(r"(cell\.oncontextmenu\s*=\s*function\s*\(\s*e\s*\)\s*\{\s*)", re.M)
if "hideTip(cell);" not in out:
    out, n = pat_ctx.subn(r"\1\n          if (typeof hideTip === 'function') { hideTip(cell); }\n          if (typeof ctxOpen !== 'undefined') { ctxOpen = true; }\n", out, count=1)
    print("OK: oncontextmenu chowa tooltip i ustawia ctxOpen=true." if n else "UWAGA: nie znalazem cell.oncontextmenu = function(e){ ... }")

# 4) Po zamkniciu menu: ctxOpen=false
# Szukamy function closeContextMenu() { ... }
if "ctxOpen = false;" not in out:
    out, n = re.subn(
        r"(function\s+closeContextMenu\s*\(\s*\)\s*\{\s*[\s\S]*?ctxMenu\.style\.display\s*=\s*\"none\";\s*)",
        r"\1\n    if (typeof ctxOpen !== 'undefined') { ctxOpen = false; }\n",
        out,
        count=1
    )
    print("OK: closeContextMenu ustawia ctxOpen=false." if n else "UWAGA: nie znalazem function closeContextMenu().")

# 5) Dodatkowo: gdy otwierasz menu, schowaj wszystkie tipy na stronie (eby aden nie zosta)
if "hideAllTips()" not in out:
    # dodaj helper po hideTip()
    out, n = re.subn(
        r"(function\s+hideTip\s*\(\s*cell\s*\)\s*\{\s*[\s\S]*?\}\s*)",
        r"\1\n\n  function hideAllTips() {\n    var tips = document.getElementsByClassName('tip');\n    for (var i=0; i<tips.length; i++) tips[i].style.display = 'none';\n  }\n",
        out,
        count=1
    )
    if n:
        print("OK: dodano hideAllTips().")
    else:
        print("UWAGA: nie znalazem function hideTip(cell) - pomijam hideAllTips().")

# i wywoaj hideAllTips() przy prawym kliku (jeli helper istnieje)
if "hideAllTips();" not in out and "function hideAllTips()" in out:
    out = out.replace("openContextMenu(cell, e.clientX, e.clientY);", "if (typeof hideAllTips === 'function') { hideAllTips(); }\n          openContextMenu(cell, e.clientX, e.clientY);")
    print("OK: oncontextmenu woa hideAllTips().")

path.write_text(out, encoding="utf-8")
print("Zapisano:", path)
print("DONE")
