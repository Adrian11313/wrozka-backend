from pathlib import Path
from datetime import datetime
import re

path = Path("app/web/templates/vq_matrix.html")
src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_fixall_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

# 1) Usu wszystko co jest PO "{% endblock %}" (bo tam nie moe by JS)
src = re.sub(r"{%\s*endblock\s*%}[\s\S]*\Z", "{% endblock %}\n", src)

# 2) Usu stare ctxMenu jeli gdzie jest w HTML (eby nie byo duplikatów)
src = re.sub(r"<!--\s*Context Menu.*?-->\s*<div[^>]*id=['\"]ctxMenu['\"][\s\S]*?</div>\s*", "", src, flags=re.I)

# 3) Wycignij JS (zostawiamy jak jest), ale usuwamy mieci AUTO-FIX i fragmenty po </script>
# Usuwamy linie AUTO-FIX
src = re.sub(r"^\s*//\s*\[AUTO-FIX\].*$", "", src, flags=re.M)

# 4) Wstaw ctxMenu HTML tu przed "{% endblock %}"
insert_menu = r"""
<!-- Context Menu (prawy klik) -->
<div id="ctxMenu" style="position:fixed; display:none; background:#111; color:#fff; border-radius:10px; padding:8px; z-index:9999; width:380px; box-shadow:0 10px 30px rgba(0,0,0,0.25);">
  <div id="ctxTitle" style="font-weight:600; margin-bottom:6px;">Historia</div>
  <div id="ctxItems"></div>
</div>

{% endblock %}
"""

src = re.sub(r"{%\s*endblock\s*%}\s*\Z", insert_menu, src)

# 5) Do rodka <script> dopisz/napraw funkcje:
# - positionTip() liczy po treci i zawsze przestawia tooltip
# - cell.oncontextmenu: chowa tooltip i pokazuje menu
# - openContextMenu/restoreFromHistory musz by wewntrz IIFE (script)

# znajd </script> w pliku
m = re.search(r"</script>", src, flags=re.I)
if not m:
    raise SystemExit("Nie znalazem </script> w pliku - wklej najpierw wersj z dziaajcym <script>.")

script_end = m.start()
before = src[:script_end]
after = src[script_end:]

# jeli w JS masz ju openContextMenu/restoreFromHistory, to najczciej s PO endblock (czyli wycite).
# my je dopiszemy na kocu JS w <script> (przed </script>), ale w bezpieczny sposób (bez duplikatów)

def has_fn(text, name):
    return re.search(r"\bfunction\s+" + re.escape(name) + r"\s*\(", text) is not None

patch_js = []

# positionTip() — nadpisujemy wersj stabiln
patch_js.append(r"""
  // --- Tooltip positioning (fix for last column) ---
  function positionTip(cell) {
    var tip = cell.getElementsByClassName("tip")[0];
    if (!tip) return;

    // reset
    tip.style.left = "6px";
    tip.style.right = "auto";

    // musi by widoczny, eby policzy rect
    tip.style.display = "block";

    var rect = tip.getBoundingClientRect();
    var pad = 10;

    // jeli wypada w prawo -> przyklej do prawej krawdzi komórki
    if (rect.right > window.innerWidth - pad) {
      tip.style.left = "auto";
      tip.style.right = "6px";
    } else {
      tip.style.left = "6px";
      tip.style.right = "auto";
    }

    // jeli nadal wypada w lewo (bardzo wski ekran)
    rect = tip.getBoundingClientRect();
    if (rect.left < pad) {
      tip.style.left = pad + "px";
      tip.style.right = "auto";
    }
  }
""")

# showTip() - upewniamy si e uywa positionTip
patch_js.append(r"""
  // --- show/hide tooltip (calls positionTip) ---
  function showTip(cell) {
    var tip = cell.getElementsByClassName("tip")[0];
    if (!tip) return;
    tip.style.display = "block";
    positionTip(cell);
  }
""")

# openContextMenu + restoreFromHistory (jeli nie ma) — dodajemy
if not has_fn(before, "openContextMenu"):
    patch_js.append(r"""
  // -------- CONTEXT MENU (RIGHT CLICK) ----------
  var ctxMenu = document.getElementById("ctxMenu");
  var ctxTitle = document.getElementById("ctxTitle");
  var ctxItems = document.getElementById("ctxItems");

  function closeContextMenu() {
    if (!ctxMenu) return;
    ctxMenu.style.display = "none";
    if (ctxItems) ctxItems.innerHTML = "";
  }

  document.addEventListener("mousedown", function(e){
    if (e.button === 2) return;
    closeContextMenu();
  });

  function openContextMenu(cell, x, y) {
    if (!ctxMenu) return;

    // ukryj tooltip na prawy klik
    hideTip(cell);

    var topicId = cell.getAttribute("data-topic-id");
    var depId = cell.getAttribute("data-department-id");
    var depName = cell.getAttribute("data-department-name") || "";

    ctxTitle.innerHTML = "Przywró • " + escapeHtml(depName);
    ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>adowanie...</div>";
    ctxMenu.style.display = "block";

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
""")

# bindCells: dodaj prawy klik jeli nie ma
if not re.search(r"\.oncontextmenu\s*=", before):
    patch_js.append(r"""
  // --- ensure right-click handler exists ---
  (function(){
    var cells = document.getElementsByClassName("cell");
    for (var i=0; i<cells.length; i++) {
      (function(cell){
        cell.oncontextmenu = function(e){
          e.preventDefault();
          openContextMenu(cell, e.clientX, e.clientY);
          return false;
        };
      })(cells[i]);
    }
  })();
""")

# wstrzyknij patch przed </script>
injected = before + "\n\n" + "\n".join(patch_js) + "\n\n" + after
path.write_text(injected, encoding="utf-8")

print("OK: Naprawiono struktur (no JS after endblock) + ctxMenu w HTML + tooltip positioning + context menu w <script>.")
print("Zapisano:", path)
