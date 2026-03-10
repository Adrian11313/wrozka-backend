from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_ctx2_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

def find_function_block(s: str, name: str) -> tuple[int,int]:
    # znajd "function NAME(" i wytnij blok klamrowy { ... }
    key = f"function {name}("
    start = s.find(key)
    if start == -1:
        return (-1,-1)

    brace = s.find("{", start)
    if brace == -1:
        return (-1,-1)

    i = brace
    depth = 0
    in_str = None
    esc = False
    while i < len(s):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
        else:
            if ch in ("'", '"'):
                in_str = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return (start, i+1)
        i += 1
    return (-1,-1)

# 1) dopnij CSS (scroll + sensowna szeroko)
css_add = """
  /* Context menu - layout */
  #ctxMenu { width: 420px !important; max-width: 70vw; }
  #ctxItems { max-height: 320px; overflow: auto; padding-right: 4px; }
"""
if css_add.strip() not in out:
    out = out.replace("</style>", css_add + "\n</style>", 1)
    print("OK: dopito CSS dla ctxMenu/ctxItems.")

# 2) patch: hide tooltip on right click (eby nie zasania menu)
# szukamy: cell.oncontextmenu = function(e){ ... openContextMenu(cell,...)
needle = "openContextMenu(cell"
idx = out.find(needle)
if idx != -1:
    # doó hideTip(cell) przed openContextMenu jeli hideTip istnieje
    out2 = out
    # tylko jeli nie ma ju hideTip w oncontextmenu
    if "oncontextmenu" in out and "hideTip(cell)" not in out:
        out2 = out2.replace(
            "openContextMenu(cell, e.clientX, e.clientY);",
            "if (typeof hideTip === 'function') { hideTip(cell); }\n          openContextMenu(cell, e.clientX, e.clientY);"
        )
        if out2 != out:
            out = out2
            print("OK: dodano chowanie tooltipa przy prawym kliku.")
else:
    print("INFO: nie znalazem openContextMenu(cell...) w bindCells – pomijam hideTip patch.")

# 3) patch openContextMenu: wstawiamy wasny renderer listy (do 10 + skrót treci)
a,b = find_function_block(out, "openContextMenu")
if a == -1:
    raise SystemExit("Nie znalazem function openContextMenu(...) w pliku vq_matrix.html")

fn = out[a:b]

# Musi istnie ctxItems i parsowanie JSON. Wstawimy kod zaraz po parsowaniu items
# Szukamy miejsca po:
#   var items = [];
#   try { items = JSON.parse(text); } catch(e) { items = []; }
marker = "try { items = JSON.parse(text); } catch(e) { items = []; }"
mpos = fn.find(marker)
if mpos == -1:
    # fallback: inne formatowanie try/catch
    marker2 = "items = JSON.parse(text)"
    mpos = fn.find(marker2)
    if mpos == -1:
        raise SystemExit("Nie znalazem parsowania JSON w openContextMenu(). Podelij t funkcj, jeli patch nie wejdzie.")
    # znajd koniec linii z JSON.parse
    line_end = fn.find(";", mpos)
    insert_after = line_end + 1
else:
    insert_after = mpos + len(marker)

inject = """

      // === AUTO: render listy historii (max 10) + skrót treci ===
      if (!items || !items.length) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Brak historii.</div>";
        return;
      }

      var html = "";
      var max = (items.length < 10) ? items.length : 10;

      for (var i=0; i<max; i++) {
        var it = items[i];
        var meta = "v" + it.new_version + " • " + formatDate(it.changed_at) + " • user_id=" + it.changed_by;

        var txt = (it.new_content && it.new_content.length) ? it.new_content : "(pusto)";
        var shortTxt = txt;
        if (shortTxt.length > 220) shortTxt = shortTxt.substring(0, 220) + "…";

        html += "<div class='ctxItem' data-hid='" + it.id + "'>"
          + "<div class='ctxMeta'>" + escapeHtml(meta) + "</div>"
          + "<div class='ctxTxt'>" + escapeHtml(shortTxt) + "</div>"
          + "</div>";
      }

      ctxItems.innerHTML = html;

      var els = ctxItems.getElementsByClassName("ctxItem");
      for (var j=0; j<els.length; j++) {
        (function(el){
          el.onclick = function(ev){
            ev.stopPropagation();
            var hid = el.getAttribute("data-hid");
            restoreFromHistory(cell, hid);
            closeContextMenu();
          };
        })(els[j]);
      }

      return;
      // === /AUTO ===
"""

# wstaw inject, ale usu stary renderer jeli jest (eby nie dublowa)
# Najprociej: wstawiamy inject i koczymy return; wic stary kod si nie wykona.
fn2 = fn[:insert_after] + inject + fn[insert_after:]

out = out[:a] + fn2 + out[b:]
print("OK: podmieniono openContextMenu() – lista historii do 10 + skrót treci.")

path.write_text(out, encoding="utf-8")
print("Zapisano:", path)
print("DONE")
