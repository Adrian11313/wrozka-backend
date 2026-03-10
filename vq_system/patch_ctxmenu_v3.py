from pathlib import Path
from datetime import datetime
import re

path = Path("app/web/templates/vq_matrix.html")
src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_ctxv3_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) upewnij si e ctxMenu HTML istnieje (przed </body>)
if 'id="ctxMenu"' not in out:
    menu_html = """
<!-- Context Menu (prawy klik) -->
<div id="ctxMenu" style="position:fixed; display:none; background:#111; color:#fff; border-radius:10px; padding:8px; z-index:9999; width:360px; box-shadow:0 10px 30px rgba(0,0,0,0.25);">
  <div id="ctxTitle" style="font-weight:600; margin-bottom:6px;">Historia</div>
  <div id="ctxItems"></div>
</div>
"""
    pos = out.lower().rfind("</body>")
    if pos == -1:
        raise SystemExit("Nie ma </body> w vq_matrix.html")
    out = out[:pos] + menu_html + out[pos:]
    print("Dodano ctxMenu HTML")

# 2) dodaj CSS (.ctxItem/.ctxMeta/.ctxTxt) do <style> jeli brakuje
if ".ctxItem" not in out:
    m = re.search(r"<style>\s*", out, re.IGNORECASE)
    if not m:
        raise SystemExit("Brak <style> w pliku")
    css = """
  /* Context menu */
  .ctxItem { padding: 8px 10px; border-radius: 8px; cursor: pointer; }
  .ctxItem:hover { background: rgba(255,255,255,0.12); }
  .ctxMeta { font-size: 11px; color: rgba(255,255,255,0.75); margin-bottom: 2px; }
  .ctxTxt { font-size: 12px; white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere; }
"""
    out = out[:m.end()] + css + out[m.end():]
    print("Dodano CSS ctxMenu")

# 3) wstrzyknij JS "na kocu IIFE" przed bindCells(); initCellMeta();
# znajdziemy ostatnie wystpienie 'bindCells();' i wstawimy kod tu przed nim
anchor = out.rfind("bindCells();")
if anchor == -1:
    raise SystemExit("Nie znalazem 'bindCells();' w <script>")

js = r'''
  // -------- CONTEXT MENU (RIGHT CLICK) v3 ----------
  var ctxMenu = document.getElementById("ctxMenu");
  var ctxTitle = document.getElementById("ctxTitle");
  var ctxItems = document.getElementById("ctxItems");

  function closeContextMenu() {
    if (!ctxMenu) return;
    ctxMenu.style.display = "none";
    if (ctxItems) ctxItems.innerHTML = "";
  }

  // zamykamy menu po klikniciu gdziekolwiek (ale NIE po prawym)
  document.addEventListener("mousedown", function(e){
    if (e.button === 2) return; // prawy klik
    closeContextMenu();
  });

  // blokujemy domylne menu globalnie (opcjonalnie)
  document.addEventListener("contextmenu", function(e){
    // nie blokuj wszdzie, tylko w komórkach - ale jak klikniesz poza cell to OK
  });

  function openContextMenu(cell, x, y) {
    if (!ctxMenu) return;

    var topicId = cell.getAttribute("data-topic-id");
    var depId = cell.getAttribute("data-department-id");
    var depName = cell.getAttribute("data-department-name") || "";
    var topicTitle = cell.getAttribute("data-topic-title") || "";

    ctxTitle.innerHTML = "Przywró • " + escapeHtml(depName);
    ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>adowanie...</div>";
    ctxMenu.style.display = "block";

    // pozycja menu pod kursorem (nie wypada poza ekran)
    var w = 380;
    var h = 340;
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

      // zabezpieczenie gdy backend zwróci HTML
      if (!text || text.trim().startsWith("<")) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Niepoprawna odpowied serwera.</div>";
        return;
      }

      var items = [];
      try { items = JSON.parse(text); } catch(e) { items = []; }

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

  function restoreFromHistory(cell, historyId) {
    var topicId = cell.getAttribute("data-topic-id");
    var departmentId = cell.getAttribute("data-department-id");
    var clientVersion = cell.getAttribute("data-version") || "1";

    var body = "topic_id=" + encodeURIComponent(topicId)
      + "&department_id=" + encodeURIComponent(departmentId)
      + "&history_id=" + encodeURIComponent(historyId)
      + "&client_version=" + encodeURIComponent(clientVersion);

    xhr("POST", "/web/positions/restore", body, "application/x-www-form-urlencoded", function(status, text){
      if (status === 401) { alert("Zaloguj si."); return; }
      if (status === 409) { alert("Konflikt wersji – odwie komórk."); return; }
      if (!(status >= 200 && status < 300)) { alert("Bd: " + status); return; }

      var p = JSON.parse(text);

      var key = topicId + "_" + departmentId;
      if (typeof tipCache !== "undefined") { delete tipCache[key]; }

      cell.setAttribute("data-content", p.content || "");
      cell.setAttribute("data-version", String(p.version));

      var contentDiv = cell.getElementsByClassName("content")[0];
      var metaDiv = cell.getElementsByClassName("vmeta")[0];

      if (p.content && p.content.length) {
        contentDiv.style.color = "#000";
        contentDiv.innerHTML = escapeHtml(p.content);
      } else {
        contentDiv.style.color = "#999";
        contentDiv.innerHTML = "-";
      }
      metaDiv.innerHTML = "v" + p.version;

      if (typeof setCellMeta === "function") {
        setCellMeta(cell, p.last_changed_at, p.last_changed_by);
      }
    });
  }
'''

# usu poprzednie definicje openContextMenu/restoreFromHistory jeli istniej (eby nie byo konfliktów)
out = re.sub(r"\n\s*// -------- CONTEXT MENU.*?function restoreFromHistory.*?\n\s*}\s*\n", "\n", out, flags=re.DOTALL)

out = out[:anchor] + js + "\n" + out[anchor:]

# 4) dopnij oncontextmenu do komórek (jeli nie ma)
if "cell.oncontextmenu" not in out:
    out = out.replace(
        "cell.onclick = function(){ openModal(cell); };",
        "cell.onclick = function(){ openModal(cell); };\n\n        cell.oncontextmenu = function(e){\n          e.preventDefault();\n          openContextMenu(cell, e.clientX, e.clientY);\n          return false;\n        };"
    )
    print("Dodano cell.oncontextmenu")
else:
    print("cell.oncontextmenu ju jest")

path.write_text(out, encoding="utf-8")
print("OK: zapisano vq_matrix.html")
