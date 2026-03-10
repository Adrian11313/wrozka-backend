import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono pliku: {path}")

src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_fix_syntax_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) Wytnij "luny JS" po </script> (to czsto psuje DOM i patchowanie)
#    Jeeli po </script> jest fragment "// -------- CONTEXT MENU", usuwamy go do koca pliku,
#    ale zostawiamy {% endblock %} i ewentualny HTML ctxMenu jeli jest.
script_close = out.rfind("</script>")
if script_close == -1:
    raise SystemExit("Nie znalazem </script> w pliku.")

after = out[script_close + len("</script>"):]
# Usuwamy cz JS po </script> zaczynajc si od "// -------- CONTEXT MENU"
m = re.search(r"\n\s*//\s*-+\s*CONTEXT MENU.*", after)
if m:
    # zostawiamy to co jest PRZED tym blokiem + kocówk z endblock
    tail = after[:m.start()]
    # wycignij endblock jeli jest dalej
    endblock_m = re.search(r"{%\s*endblock\s*%}", after[m.start():])
    if endblock_m:
        tail += "\n\n{% endblock %}\n"
    after = tail
    out = out[:script_close + len("</script>")] + after
    print("OK: wycito luny blok CONTEXT MENU po </script> (jeli by).")
else:
    print("OK: nie wykryto lunego bloku CONTEXT MENU po </script>.")

# 2) Upewnij si e mamy HTML dla ctxMenu (POZA <script>)
if 'id="ctxMenu"' not in out:
    # wstaw tu po </script>
    insert = """
<!-- Context Menu (prawy klik) -->
<div id="ctxMenu" style="position:fixed; display:none; background:#111; color:#fff; border-radius:10px; padding:8px; z-index:9999; width:360px; box-shadow:0 10px 30px rgba(0,0,0,0.25);">
  <div id="ctxTitle" style="font-weight:600; margin-bottom:6px;">Historia</div>
  <div id="ctxItems"></div>
</div>
"""
    out = out.replace("</script>", "</script>" + insert, 1)
    print("OK: dodano HTML ctxMenu (po </script>).")
else:
    print("OK: HTML ctxMenu ju istnieje.")

# 3) Dopisz CSS dla ctxMenu/ctxItems (scroll + czytelno) w <style>
#    Doklejamy na kocu <style> (pierwszy blok style)
style_m = re.search(r"<style>(.*?)</style>", out, re.DOTALL)
if not style_m:
    raise SystemExit("Nie znalazem bloku <style>...</style>.")

style_block = style_m.group(0)
style_body = style_m.group(1)

if "#ctxItems" not in style_body:
    style_body += """
  /* Context menu */
  #ctxMenu { max-height: 360px; overflow: hidden; }
  #ctxItems { max-height: 300px; overflow: auto; padding-right: 4px; }
  .ctxItem { padding: 6px 8px; border-radius: 8px; cursor: pointer; }
  .ctxItem:hover { background: rgba(255,255,255,0.12); }
  .ctxMeta { font-size: 11px; color: rgba(255,255,255,0.75); margin-bottom: 2px; }
  .ctxTxt { font-size: 12px; white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere; }
"""
    new_style = "<style>" + style_body + "</style>"
    out = out[:style_m.start()] + new_style + out[style_m.end():]
    print("OK: dopisano CSS ctxMenu/ctxItems.")
else:
    print("OK: CSS ctxMenu ju jest (pomijam).")

# 4) Wstrzyknij poprawny kod JS context-menu W RODKU istniejcego (function(){ ... }) IIFE
#    Wstawiamy tu przed "bindCells();" (jeli istnieje), inaczej przed kocem IIFE "})();"
insert_point = out.find("bindCells();")
if insert_point == -1:
    insert_point = out.rfind("})();")
    if insert_point == -1:
        raise SystemExit("Nie znalazem miejsca w JS (bindCells() ani koca IIFE).")

ctx_js = r"""
  // -------- CONTEXT MENU (RIGHT CLICK) FIXED ----------
  var ctxOpen = false;

  function hideAllTips() {
    var tips = document.getElementsByClassName("tip");
    for (var i=0; i<tips.length; i++) tips[i].style.display = "none";
  }

  var ctxMenu = document.getElementById("ctxMenu");
  var ctxTitle = document.getElementById("ctxTitle");
  var ctxItems = document.getElementById("ctxItems");

  function closeContextMenu() {
    if (!ctxMenu) return;
    ctxMenu.style.display = "none";
    if (ctxItems) ctxItems.innerHTML = "";
    ctxOpen = false;
  }

  // zamykamy menu po klikniciu gdziekolwiek (poza prawym)
  document.addEventListener("mousedown", function(e){
    if (e.button === 2) return; // prawy klik
    closeContextMenu();
  });

  function openContextMenu(cell, x, y) {
    if (!ctxMenu || !ctxTitle || !ctxItems) return;

    // menu ma przykry tooltip
    ctxOpen = true;
    hideAllTips();

    var topicId = cell.getAttribute("data-topic-id");
    var depId = cell.getAttribute("data-department-id");
    var depName = cell.getAttribute("data-department-name") || "";

    ctxTitle.innerHTML = "Przywró • " + escapeHtml(depName);
    ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>adowanie...</div>";
    ctxMenu.style.display = "block";

    // pozycja menu pod kursorem (nie wypada poza ekran)
    var w = 380;
    var h = 360;
    var px = Math.min(x + 8, window.innerWidth - w - 10);
    var py = Math.min(y + 8, window.innerHeight - h - 10);
    ctxMenu.style.left = px + "px";
    ctxMenu.style.top = py + "px";

    xhr("GET", "/web/positions/history/by_cell/" + topicId + "/" + depId, null, null, function(status, text){
      if (status === 401) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Zaloguj si.</div>";
        return;
      }
      if (!(status >= 200 && status < 300)) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Bd: " + status + "</div>";
        return;
      }

      if (!text || text.trim().startsWith("<")) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Niepoprawna odpowied serwera.</div>";
        return;
      }

      var items = [];
      try { items = text ? JSON.parse(text) : []; } catch(e) { items = []; }

      if (!items.length) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Brak historii.</div>";
        return;
      }

      var html = "";
      for (var i=0; i<items.length && i<10; i++) {
        var it = items[i];
        var meta = "v" + it.new_version + " • " + formatDate(it.changed_at) + " • user_id=" + it.changed_by;
        var txt = (it.new_content && it.new_content.length) ? it.new_content : "(pusto)";
        html += "<div class='ctxItem' data-hid='" + it.id + "'>"
          + "<div class='ctxMeta'>" + escapeHtml(meta) + "</div>"
          + "<div class='ctxTxt'>" + escapeHtml(txt) + "</div>"
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
    });
  }

  // podpinka prawy klik + chowanie tooltipu
  (function bindRightClick(){
    var cells = document.getElementsByClassName("cell");
    for (var i=0; i<cells.length; i++) {
      (function(cell){
        cell.oncontextmenu = function(e){
          e.preventDefault();
          openContextMenu(cell, e.clientX, e.clientY);
          return false;
        };
        // jeli tooltip dziaa, to przy wejciu poka tylko gdy menu NIE jest otwarte
        var oldEnter = cell.onmouseenter;
        cell.onmouseenter = function(){
          if (ctxOpen) return;
          if (typeof oldEnter === "function") oldEnter();
        };
      })(cells[i]);
    }
  })();
"""

# usu starsze wstrzyknicia jeli istniej (eby nie dublowa)
out = re.sub(r"\n\s*//\s*-+\s*CONTEXT MENU.*?bindRightClick\(\)\s*\)\(\);\s*\n", "\n", out, flags=re.DOTALL)

out = out[:insert_point] + ctx_js + "\n\n" + out[insert_point:]
print("OK: wstrzyknito poprawny kod context-menu do JS.")

path.write_text(out, encoding="utf-8")
print("Zapisano:", path)
print("DONE")
