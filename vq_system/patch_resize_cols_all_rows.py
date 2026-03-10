import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono pliku: {path}")

src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_col_all_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# --- 1) CSS: uchwyt w TD te + wyszy z-index ---
css_add = r"""
  /* ===== Column resize (Excel-like) - grips in TH + TD ===== */
  .vqTable th, .vqTable td { position: relative; }
  .vqTable .col-resizer{
    position:absolute;
    top:0;
    right:-4px;
    width:10px;
    height:100%;
    cursor: col-resize;
    user-select:none;
    z-index: 200; /* above tooltip */
  }
  body.resizing, body.resizing *{
    cursor: col-resize !important;
    user-select: none !important;
  }
"""

if ".vqTable .col-resizer" not in out:
    # wstaw przed </style>
    out = re.sub(r"</style>", css_add + "\n</style>", out, count=1, flags=re.IGNORECASE)
    print("OK: dopisano CSS dla col-resizer w TH+TD.")
else:
    print("INFO: CSS dla col-resizer ju istnieje (pomijam).")

# --- 2) JS: dodaj flag isResizing, eby tooltip nie wchodzi w drog ---
if "var isResizing =" not in out:
    out = re.sub(
        r"(var\s+ctxOpen\s*=\s*false\s*;[^\n]*\n)",
        r"\1  var isResizing = false; // when resizing columns/rows, disable tooltip hover\n",
        out,
        count=1
    )
    print("OK: dodano var isResizing.")
else:
    print("INFO: var isResizing ju jest (pomijam).")

# podmie warunek w loadHistory, aby blokowa te przy resize
out = re.sub(
    r"if\s*\(\s*typeof\s+ctxOpen\s*!==\s*'undefined'\s*&&\s*ctxOpen\s*\)\s*return\s*;",
    "if ((typeof ctxOpen !== 'undefined' && ctxOpen) || (typeof isResizing !== 'undefined' && isResizing)) return;",
    out,
    count=1
)

# --- 3) JS: podmie enableColumnResize() na wersj, która dziaa z kadego wiersza ---
new_enable_col = r"""
  // ===== Column resize (Excel-like) - works from ANY row (TH + TD) =====
  function enableColumnResize() {
    var table = document.getElementsByClassName("vqTable")[0];
    if (!table) return;

    // helper: get all rows
    var rows = table.getElementsByTagName("tr");
    if (!rows || !rows.length) return;

    // add grips to every cell in every row except the last column
    for (var r = 0; r < rows.length; r++) {
      var cells = rows[r].children;
      if (!cells || cells.length < 2) continue;

      for (var c = 0; c < cells.length - 1; c++) {
        (function(cell, colIndex){
          // avoid duplicates
          if (cell.getElementsByClassName("col-resizer")[0]) return;

          var grip = document.createElement("div");
          grip.className = "col-resizer";
          cell.appendChild(grip);

          grip.addEventListener("mousedown", function(e){
            e.preventDefault();
            e.stopPropagation();

            isResizing = true;
            if (typeof hideAllTips === "function") hideAllTips();
            document.body.classList.add("resizing");

            var startX = e.clientX;

            // width bazujemy na komórce z tego samego wiersza/kolumny
            var startW = cell.getBoundingClientRect().width;

            // ustaw szeroko KOLUMNY (wszystkie wiersze)
            function setColWidth(px) {
              for (var rr = 0; rr < rows.length; rr++) {
                var rcells = rows[rr].children;
                if (!rcells || rcells.length <= colIndex) continue;
                rcells[colIndex].style.width = px + "px";
              }
            }

            // init fixed width
            setColWidth(Math.max(80, Math.round(startW)));

            function onMove(ev){
              var dx = ev.clientX - startX;
              var w = Math.max(80, Math.round(startW + dx));
              setColWidth(w);
              ev.preventDefault();
            }

            function onUp(){
              document.removeEventListener("mousemove", onMove);
              document.removeEventListener("mouseup", onUp);
              document.body.classList.remove("resizing");
              isResizing = false;
            }

            document.addEventListener("mousemove", onMove);
            document.addEventListener("mouseup", onUp);
          });
        })(cells[c], c);
      }
    }
  }
"""

# wymie ca funkcj enableColumnResize (jeli istnieje)
m = re.search(r"\n\s*function\s+enableColumnResize\s*\(\)\s*\{.*?\n\s*\}\n", out, flags=re.DOTALL)
if not m:
    raise SystemExit("Nie znalazem function enableColumnResize() w pliku. Wklej mi fragment JS wokó tej funkcji, to zrobi patch 1:1.")
out = out[:m.start()] + "\n" + new_enable_col + "\n" + out[m.end():]
print("OK: podmieniono enableColumnResize() na wersj dla wszystkich wierszy.")

path.write_text(out, encoding="utf-8")
print("Zapisano:", path)
print("DONE")
