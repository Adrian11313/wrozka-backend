from pathlib import Path
from datetime import datetime
import re

path = Path("app/web/templates/vq_matrix.html")
src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_ctx_list_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) Dopnij CSS, eby menu miao scroll i byo czytelne
if "#ctxMenu" not in out:
    # jeli masz ctxMenu jako inline-style to i tak dopniemy minimalny CSS
    pass

css_add = r"""
  /* Context menu - layout */
  #ctxMenu { width: 420px !important; max-width: 70vw; }
  #ctxItems { max-height: 320px; overflow: auto; padding-right: 4px; }
"""

if css_add.strip() not in out:
    out = out.replace("</style>", css_add + "\n</style>", 1)
    print("OK: dopito CSS dla ctxMenu/ctxItems.")

# 2) Napraw blok budowania listy w openContextMenu (wymusza 10 pozycji + tre)
# Szukamy fragmentu: var html = ""; for (var i=0; i<items.length ... ) ... ctxItems.innerHTML = html;
pat = re.compile(
    r"var\s+html\s*=\s*\"\"\s*;\s*for\s*\(\s*var\s+i\s*=\s*0\s*;[\s\S]*?ctxItems\.innerHTML\s*=\s*html\s*;",
    re.MULTILINE
)

replacement = r"""
      var html = "";
      var max = (items.length < 10) ? items.length : 10;

      for (var i=0; i<max; i++) {
        var it = items[i];

        var meta = "v" + it.new_version + " • " + formatDate(it.changed_at) + " • user_id=" + it.changed_by;

        var txt = (it.new_content && it.new_content.length) ? it.new_content : "(pusto)";

        // skró w menu, eby byo czytelnie (pena tre jest w tooltipie / po klikniciu i tak przywracasz)
        var shortTxt = txt;
        if (shortTxt.length > 220) shortTxt = shortTxt.substring(0, 220) + "…";

        html += "<div class='ctxItem' data-hid='" + it.id + "'>"
          + "<div class='ctxMeta'>" + escapeHtml(meta) + "</div>"
          + "<div class='ctxTxt'>" + escapeHtml(shortTxt) + "</div>"
          + "</div>";
      }

      ctxItems.innerHTML = html;
"""

m = pat.search(out)
if not m:
    raise SystemExit("Nie znalazem bloku 'var html... ctxItems.innerHTML = html' w openContextMenu(). Wklej mi prosz sam funkcj openContextMenu z pliku, to zrobi patch pod 100% zgodny ukad.")
out = pat.sub(replacement, out, count=1)
print("OK: podmieniono budowanie listy wpisów w openContextMenu().")

# 3) Ustaw tytu menu na 'Przywró' (eby nie mylio si z tooltipem 'Historia')
out = out.replace(
    'ctxTitle.innerHTML = "Przywró • " + escapeHtml(depName);',
    'ctxTitle.innerHTML = "Przywró • " + escapeHtml(depName);'
)
out = out.replace(
    'ctxTitle.innerHTML = "Historia • " + escapeHtml(depName);',
    'ctxTitle.innerHTML = "Przywró • " + escapeHtml(depName);'
)

path.write_text(out, encoding="utf-8")
print("Zapisano:", path)
print("DONE")
