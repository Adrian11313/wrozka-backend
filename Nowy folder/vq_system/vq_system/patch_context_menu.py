import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono pliku: {path}")

src = path.read_text(encoding="utf-8")

# backup
bak = path.with_suffix(path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) Dodaj HTML menu kontekstowe przed </body> / przed </script> koncowym (jeli nie ma)
if 'id="ctxMenu"' not in out:
    insert_point = out.rfind("</script>")
    if insert_point == -1:
        raise SystemExit("Nie znalazem </script> w vq_matrix.html — wklej rcznie, albo podelij kocówk pliku.")
    menu_html = r'''

<!-- Context Menu (prawy klik) -->
<div id="ctxMenu" style="position:fixed; display:none; background:#111; color:#fff; border-radius:10px; padding:8px; z-index:9999; width:280px; box-shadow:0 10px 30px rgba(0,0,0,0.25);">
  <div id="ctxTitle" style="font-weight:600; margin-bottom:6px;">Opcje</div>
  <div id="ctxItems"></div>
</div>
'''
    out = out[:insert_point] + menu_html + out[insert_point:]
    print("Dodano HTML: ctxMenu")

# 2) Dodaj CSS dla menu (jeli nie ma) - dopisz w <style> (pierwszy blok)
if ".ctxItem" not in out:
    m = re.search(r"<style>\s*", out)
    if not m:
        raise SystemExit("Nie znalazem <style> — nie mog dopisa CSS. Podelij pocztek pliku.")
    css = r'''
  /* Context menu */
  .ctxItem { padding: 6px 8px; border-radius: 8px; cursor: pointer; }
  .ctxItem:hover { background: rgba(255,255,255,0.12); }
  .ctxMeta { font-size: 11px; color: rgba(255,255,255,0.75); margin-bottom: 2px; }
  .ctxTxt { font-size: 12px; white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere; }
'''
    out = out[:m.end()] + css + out[m.end():]
    print("Dodano CSS: ctxMenu")

# 3) JS: wstaw funkcje menu kontekstowego (jeli nie istniej)
if "function openContextMenu(cell" not in out:
    # Wstawiamy przed bindCells() wywoaniem, najlepiej przed "function bindCells()"
    m = re.search(r"\n\s*function\s+bindCells\s*\(\s*\)\s*\{", out)
    if not m:
        raise SystemExit("Nie znalazem function bindCells() — nie mog wstawi JS. Podelij fragment JS.")
    insert_at = m.start()

    js = r'''

  // -------- CONTEXT MENU (RIGHT CLICK) ----------
  var ctxMenu = document.getElementById("ctxMenu");
  var ctxTitle = document.getElementById("ctxTitle");
  var ctxItems = document.getElementById("ctxItems");

  function closeContextMenu() {
    if (!ctxMenu) return;
    ctxMenu.style.display = "none";
    if (ctxItems) ctxItems.innerHTML = "";
  }

  document.addEventListener("click", function(){ closeContextMenu(); });
  document.addEventListener("scroll", function(){ closeContextMenu(); }, true);

  function openContextMenu(cell, x, y) {
    if (!ctxMenu) return;

    var topicId = cell.getAttribute("data-topic-id");
    var depId = cell.getAttribute("data-department-id");
    var depName = cell.getAttribute("data-department-name") || "";

    ctxTitle.innerHTML = "Historia • " + escapeHtml(depName);
    ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>adowanie...</div>";
    ctxMenu.style.display = "block";

    // pozycja menu (eby nie wyjechao poza ekran)
    var w = 300;
    var h = 200;
    var px = Math.min(x, window.innerWidth - w - 10);
    var py = Math.min(y, window.innerHeight - h - 10);
    ctxMenu.style.left = px + "px";
    ctxMenu.style.top = py + "px";

    // Pobierz histori
    xhr("GET", "/web/positions/history/by_cell/" + topicId + "/" + depId, null, null, function(status, text){
      if (!(status >= 200 && status < 300)) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Bd: " + status + "</div>";
        return;
      }

      var items = [];
      try { items = text ? JSON.parse(text) : []; } catch(e) { items = []; }

      if (!items.length) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Brak historii.</div>";
        return;
      }

      // Minimalnie: przywró pierwszy rekord (najnowszy) jako "restore"
      var it = items[0];
      var meta = "v" + it.new_version + " • " + formatDate(it.changed_at) + " • user_id=" + it.changed_by;

      ctxItems.innerHTML =
        "<div class='ctxItem' id='ctxRestore'>" +
          "<div class='ctxMeta'>Przywró</div>" +
          "<div class='ctxTxt'>" + escapeHtml(meta) + "</div>" +
        "</div>";

      var btn = document.getElementById("ctxRestore");
      if (btn) {
        btn.onclick = function(ev){
          ev.stopPropagation();
          restoreFromHistory(cell, it.id);
          closeContextMenu();
        };
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
    out = out[:insert_at] + js + out[insert_at:]
    print("Dodano JS: openContextMenu/restoreFromHistory")

# 4) JS: dopnij oncontextmenu do komórek w bindCells()
# Szukamy fragmentu "cell.onclick = function(){ openModal(cell); };"
# i dokadamy poniej obsug prawego kliku, jeli jej nie ma.
if "oncontextmenu" not in out:
    out2 = re.sub(
        r"(cell\.onclick\s*=\s*function\s*\(\)\s*\{\s*openModal\(cell\);\s*\}\s*;)",
        r"""\1

        cell.oncontextmenu = function(e){
          e.preventDefault();
          openContextMenu(cell, e.clientX, e.clientY);
          return false;
        };""",
        out,
        count=1
    )
    if out2 == out:
        raise SystemExit("Nie udao si znale miejsca na wstawienie oncontextmenu (cell.onclick...). Podelij bindCells().")
    out = out2
    print("Dodano: cell.oncontextmenu (blokuje menu przegldarki)")
else:
    print("OK: oncontextmenu ju istnieje")

path.write_text(out, encoding="utf-8")
print("Zapisano zmiany w:", path)
print("DONE")
