import re
from pathlib import Path
from datetime import datetime

TEMPLATE = Path("app/web/templates/vq_matrix.html")
if not TEMPLATE.exists():
    raise SystemExit(f"Nie znaleziono pliku: {TEMPLATE}")

src = TEMPLATE.read_text(encoding="utf-8")

bak = TEMPLATE.with_suffix(TEMPLATE.suffix + ".bak_resize_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) Dodaj class na tabel (eby JS mia stabilny selektor)
# Szukamy: <table ... style="table-layout: fixed; width: 100%;">
table_pat = re.compile(r'(<table\b)([^>]*\bstyle\s*=\s*"[^"]*table-layout:\s*fixed[^"]*"\s*)([^>]*>)', re.IGNORECASE)
m = table_pat.search(out)
if not m:
    print("WARN: nie znalazem tabeli z table-layout: fixed. Patch spróbuje po <table cellpadding=\"8\" ...>.")
    table_pat2 = re.compile(r'(<table\b)([^>]*\bcellpadding\s*=\s*"\s*8\s*"[^>]*)(>)', re.IGNORECASE)
    m2 = table_pat2.search(out)
    if not m2:
        raise SystemExit("Nie znalazem <table ...>. Nie wiem gdzie doda resize.")
    # jeli nie ma class
    if re.search(r'\bclass\s*=', m2.group(2), re.IGNORECASE):
        out = out[:m2.start()] + m2.group(1) + m2.group(2) + m2.group(3) + out[m2.end():]
    else:
        out = out[:m2.start()] + m2.group(1) + m2.group(2) + ' class="vqTable"' + m2.group(3) + out[m2.end():]
else:
    # dodaj class="vqTable" jeli nie ma
    attrs = m.group(2)
    if re.search(r'\bclass\s*=', attrs, re.IGNORECASE):
        # dopisz vqTable do istniejcej klasy
        def add_class(match):
            val = match.group(1)
            if "vqTable" in val.split():
                return match.group(0)
            return f'class="{val} vqTable"'
        attrs2 = re.sub(r'class\s*=\s*"([^"]*)"', add_class, attrs, flags=re.IGNORECASE)
        out = out[:m.start()] + m.group(1) + attrs2 + m.group(3) + out[m.end():]
    else:
        out = out[:m.start()] + m.group(1) + attrs + ' class="vqTable"' + m.group(3) + out[m.end():]

# 2) Dodaj CSS dla uchwytu i trybu resize (w <style>)
# wstawiamy przed </style> jeli nie istnieje
css_snippet = r"""
  /* ===== Column resize (Excel-like) ===== */
  .vqTable th { position: relative; }
  .vqTable th .col-resizer{
    position:absolute;
    top:0;
    right:-4px;
    width:8px;
    height:100%;
    cursor: col-resize;
    user-select:none;
    z-index: 60;
  }
  body.resizing, body.resizing *{
    cursor: col-resize !important;
    user-select: none !important;
  }
"""
if "col-resizer" not in out:
    style_close = out.lower().find("</style>")
    if style_close == -1:
        raise SystemExit("Nie znalazem </style> w vq_matrix.html")
    out = out[:style_close] + css_snippet + "\n" + out[style_close:]
    print("Dodano CSS: col-resizer")

# 3) Dodaj JS: enableColumnResize() i wywoanie na starcie
# Szukamy koca IIFE: bindCells(); initCellMeta(); })();
# ale bezpieczniej: wstawiamy przed 'bindCells();' jeli istnieje, inaczej przed kocem '(function(){ ... })();'
js_func = r"""
  // ===== Column resize (Excel-like) =====
  function enableColumnResize() {
    var table = document.getElementsByClassName("vqTable")[0];
    if (!table) return;

    // bierzemy tylko nagówki kolumn dziaów (pierwszy TH to "Temat", reszta to dziay)
    var headerRow = table.getElementsByTagName("tr")[0];
    if (!headerRow) return;

    var ths = headerRow.getElementsByTagName("th");
    if (!ths || !ths.length) return;

    // dodaj uchwyty do wszystkich th oprócz pierwszego (ale moesz zmieni jeli chcesz)
    for (var i = 1; i < ths.length; i++) {
      (function(th){
        // nie dodawaj drugi raz
        var existing = th.getElementsByClassName("col-resizer")[0];
        if (existing) return;

        var grip = document.createElement("div");
        grip.className = "col-resizer";
        th.appendChild(grip);

        grip.addEventListener("mousedown", function(e){
          e.preventDefault();
          e.stopPropagation();

          document.body.classList.add("resizing");

          var startX = e.clientX;
          var startW = th.offsetWidth;

          // ustawiamy width w px (eby byo stabilnie)
          th.style.width = startW + "px";

          function onMove(ev){
            var dx = ev.clientX - startX;
            var w = Math.max(80, startW + dx); // min 80px
            th.style.width = w + "px";
          }

          function onUp(){
            document.removeEventListener("mousemove", onMove);
            document.removeEventListener("mouseup", onUp);
            document.body.classList.remove("resizing");
          }

          document.addEventListener("mousemove", onMove);
          document.addEventListener("mouseup", onUp);
        });
      })(ths[i]);
    }
  }
"""

if "function enableColumnResize()" not in out:
    # wstaw funkcj przed bindCells(); jeli jest
    idx = out.find("bindCells();")
    if idx != -1:
        out = out[:idx] + js_func + "\n" + out[idx:]
        print("Dodano JS: enableColumnResize()")
    else:
        # fallback: wstaw przed kocem IIFE (przed "})();")
        idx2 = out.rfind("})();")
        if idx2 == -1:
            raise SystemExit("Nie znalazem miejsca na JS (brak bindCells(); i brak '})();').")
        out = out[:idx2] + js_func + "\n" + out[idx2:]
        print("Dodano JS: enableColumnResize() (fallback)")

# dopisz wywoanie po bindCells/initCellMeta
if "enableColumnResize();" not in out:
    # najpierw spróbuj po initCellMeta();
    mcall = re.search(r'initCellMeta\(\);\s*', out)
    if mcall:
        insert_at = mcall.end()
        out = out[:insert_at] + "\n  enableColumnResize();\n" + out[insert_at:]
        print("Dodano wywoanie: enableColumnResize() po initCellMeta()")
    else:
        # po bindCells();
        mcall2 = re.search(r'bindCells\(\);\s*', out)
        if mcall2:
            insert_at = mcall2.end()
            out = out[:insert_at] + "\n  enableColumnResize();\n" + out[insert_at:]
            print("Dodano wywoanie: enableColumnResize() po bindCells()")
        else:
            print("WARN: nie znalazem bindCells()/initCellMeta() - nie dodano wywoania. Dodaj rcznie enableColumnResize(); na kocu IIFE.")

TEMPLATE.write_text(out, encoding="utf-8")
print("Zapisano:", TEMPLATE)
print("DONE")
