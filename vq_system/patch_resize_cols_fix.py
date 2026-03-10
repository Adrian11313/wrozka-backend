from pathlib import Path
from datetime import datetime
import re

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono: {path}")

src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_resize_fix_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) Wymu poprawny TH dla dziaów (kady ma resizer)
# Szukamy typowego fragmentu w ptli departments:
# <th style="min-width:220px;">{{ d.name }}</th>
out2, n = re.subn(
    r'<th([^>]*)>\s*{{\s*d\.name\s*}}\s*</th>',
    r'<th\1 class="vqTh"><div class="thLabel">{{ d.name }}</div><div class="col-resizer" title="Przecignij aby zmieni szeroko"></div></th>',
    out
)
if n == 0:
    raise SystemExit("Nie znalazem nagówków dziaów w formie <th ...>{{ d.name }}</th>. Wklej mi 5-10 linii z nagówka tabeli (z ptl departments).")
out = out2
print("OK: Dodano resizer do", n, "nagówków dziaów")

# 2) Dopnij CSS dla uchwytów (jeli nie ma)
if "/* Column resize handles (v2) */" not in out:
    css_block = r"""
  /* Column resize handles (v2) */
  th.vqTh { position: relative; padding-right: 14px; }
  th.vqTh .thLabel { pointer-events: none; }
  .col-resizer{
    position:absolute;
    right:0;
    top:0;
    width:10px;
    height:100%;
    cursor: col-resize;
    user-select:none;
    z-index: 10;
    background: transparent;
  }
  .col-resizer:after{
    content:"";
    position:absolute;
    left:4px;
    top:12%;
    width:2px;
    height:76%;
    background: rgba(0,0,0,0.22);
    border-radius:2px;
  }
  th.vqTh:hover .col-resizer:after{ background: rgba(0,0,0,0.45); }
  body.vqResizing * { cursor: col-resize !important; user-select: none !important; }
"""
    out_css = re.sub(r"</style>", css_block + "\n</style>", out, count=1, flags=re.IGNORECASE)
    if out_css == out:
        raise SystemExit("Nie znalazem </style> – nie mam gdzie dopi CSS.")
    out = out_css
    print("OK: Dopisano CSS resizera")
else:
    print("CSS resizera ju jest – pomijam")

# 3) Podmie / dodaj enableColResize() na wersj pointer-events i pewne selektory
# Usuwamy star funkcj jeli istnieje (eby nie mie 2 wersji)
out = re.sub(r"\n\s*// -------- COLUMN RESIZE.*?function enableColResize\(\)\{.*?\n\s*\}\n", "\n", out, flags=re.DOTALL)

js_block = r"""
  // -------- COLUMN RESIZE (headers) v2 ----------
  function enableColResize(){
    var table = document.querySelector("table");
    if (!table) return;

    var headerRow = table.querySelector("tr");
    if (!headerRow) return;

    var ths = headerRow.querySelectorAll("th");
    if (!ths || !ths.length) return;

    function setColWidth(colIndex, px){
      var minPx = 140;
      px = Math.max(minPx, px);

      for (var r = 0; r < table.rows.length; r++){
        var row = table.rows[r];
        if (!row || !row.cells) continue;
        var cell = row.cells[colIndex];
        if (!cell) continue;
        cell.style.width = px + "px";
        cell.style.minWidth = px + "px";
        cell.style.maxWidth = px + "px";
      }
    }

    for (var i = 0; i < ths.length; i++){
      (function(idx){
        var th = ths[idx];
        var handle = th.querySelector(".col-resizer");
        if (!handle) return;

        handle.addEventListener("pointerdown", function(e){
          e.preventDefault();
          e.stopPropagation();

          document.body.classList.add("vqResizing");
          handle.setPointerCapture(e.pointerId);

          var startX = e.clientX;
          var startW = th.getBoundingClientRect().width;

          function onMove(ev){
            var dx = ev.clientX - startX;
            setColWidth(idx, Math.round(startW + dx));
          }

          function onUp(ev){
            document.removeEventListener("pointermove", onMove);
            document.removeEventListener("pointerup", onUp);
            try { handle.releasePointerCapture(e.pointerId); } catch(_) {}
            document.body.classList.remove("vqResizing");
          }

          document.addEventListener("pointermove", onMove);
          document.addEventListener("pointerup", onUp);
        }, true);
      })(i);
    }
  }
"""

# Wstawiamy JS block tu przed kocem IIFE (przed bindCells/initCellMeta, jeli s)
anchor = "  bindCells();\n  initCellMeta();"
if anchor in out:
    out = out.replace(anchor, js_block + "\n" + anchor + "\n  enableColResize();")
    print("OK: Wpito enableColResize() i wywoanie po initCellMeta()")
else:
    # fallback: przed "})();"
    out2 = re.sub(r"\n\}\)\(\);\s*</script>", "\n" + js_block + "\n  enableColResize();\n})();\n</script>", out, count=1, flags=re.DOTALL)
    if out2 == out:
        raise SystemExit("Nie znalazem koca skryptu '</script>' / '})();' – nie wiem gdzie dopi enableColResize().")
    out = out2
    print("OK: Wpito enableColResize() (fallback)")

# 4) Zapis
path.write_text(out, encoding="utf-8")
print("Zapisano:", path)
print("DONE")
