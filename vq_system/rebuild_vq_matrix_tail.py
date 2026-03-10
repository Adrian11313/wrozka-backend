from pathlib import Path
from datetime import datetime
import re

path = Path("app/web/templates/vq_matrix.html")
src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_rebuild_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

# zostawiamy wszystko PRZED pierwszym <script ...>
m = re.search(r"<script\b[^>]*>", src, flags=re.IGNORECASE)
if not m:
    raise SystemExit("Nie znalazem <script> w vq_matrix.html")

prefix = src[:m.start()]

# budujemy od nowa poprawny blok script + ctxMenu + endblock
new_tail = r'''
<script type="text/javascript">
(function(){
  var backdrop = document.getElementById("backdrop");
  var modalTitle = document.getElementById("modalTitle");
  var modalSub = document.getElementById("modalSub");
  var modalText = document.getElementById("modalText");
  var modalMsg = document.getElementById("modalMsg");
  var btnCancel = document.getElementById("btnCancel");
  var btnSave = document.getElementById("btnSave");

  var currentCell = null;

  function xhr(method, url, body, contentType, cb) {
    var r = new XMLHttpRequest();
    r.open(method, url, true);
    if (contentType) r.setRequestHeader("Content-Type", contentType);
    r.onreadystatechange = function() {
      if (r.readyState !== 4) return;
      cb(r.status, r.responseText);
    };
    r.send(body);
  }

  function escapeHtml(s) {
    s = String(s);
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\"/g,"&quot;").replace(/\'/g,"&#39;");
  }

  function formatDate(iso) {
    if (!iso) return "-";
    var s = String(iso);
    s = s.replace("T"," ");
    s = s.replace("Z","");
    if (s.indexOf(".") !== -1) s = s.split(".")[0];
    return s;
  }

  function setCellMeta(cell, changedAt, changedBy) {
    var el = cell.getElementsByClassName("cellmeta")[0];
    if (!el) return;

    if (!changedAt && (changedBy === null || changedBy === undefined)) {
      el.innerHTML = "<span class='muted'>—</span>";
      return;
    }

    var at = formatDate(changedAt);
    var by = (changedBy === null || changedBy === undefined) ? "-" : String(changedBy);
    el.innerHTML = escapeHtml(at) + " • <span class='u'>" + escapeHtml(by) + "</span>";
  }

  // -------- EDIT MODAL ----------
  function openModal(cell) {
    currentCell = cell;
    modalMsg.style.color = "#666";
    modalMsg.innerHTML = "";

    var topicId = cell.getAttribute("data-topic-id");
    var depId = cell.getAttribute("data-department-id");

    modalTitle.innerHTML = cell.getAttribute("data-topic-title");
    modalSub.innerHTML = "Dzia: " + cell.getAttribute("data-department-name");

    xhr("GET", "/web/positions/by_cell/" + topicId + "/" + depId, null, null, function(status, text){
      if (status === 401) {
        modalMsg.style.color = "#b00020";
        modalMsg.innerHTML = "Zaloguj si.";
        backdrop.style.display = "flex";
        return;
      }
      if (status >= 200 && status < 300) {
        var p = null;
        try { p = text ? JSON.parse(text) : null; } catch(e) { p = null; }

        if (p) {
          cell.setAttribute("data-content", p.content || "");
          cell.setAttribute("data-version", String(p.version));
          setCellMeta(cell, p.last_changed_at, p.last_changed_by);
        } else {
          cell.setAttribute("data-content", "");
          cell.setAttribute("data-version", "1");
          setCellMeta(cell, null, null);
        }

        modalText.value = cell.getAttribute("data-content") || "";
        backdrop.style.display = "flex";
        return;
      }
      modalMsg.style.color = "#b00020";
      modalMsg.innerHTML = "Bd: " + status;
      backdrop.style.display = "flex";
    });
  }

  function closeModal() {
    backdrop.style.display = "none";
    currentCell = null;
  }

  btnCancel.onclick = closeModal;

  btnSave.onclick = function(){
    if (!currentCell) return;

    modalMsg.style.color = "#666";
    modalMsg.innerHTML = "";

    var topicId = currentCell.getAttribute("data-topic-id");
    var departmentId = currentCell.getAttribute("data-department-id");
    var clientVersion = currentCell.getAttribute("data-version") || "1";
    var content = modalText.value || "";

    var body = "topic_id=" + encodeURIComponent(topicId)
      + "&department_id=" + encodeURIComponent(departmentId)
      + "&content=" + encodeURIComponent(content)
      + "&client_version=" + encodeURIComponent(clientVersion);

    xhr("POST", "/web/positions/upsert", body, "application/x-www-form-urlencoded", function(status, text){
      if (status === 401) {
        modalMsg.style.color = "#b00020";
        modalMsg.innerHTML = "Zaloguj si.";
        return;
      }
      if (status === 409) {
        modalMsg.style.color = "#b00020";
        modalMsg.innerHTML = "Konflikt wersji. Otwórz komórk ponownie i zapisz.";
        return;
      }
      if (!(status >= 200 && status < 300)) {
        modalMsg.style.color = "#b00020";
        modalMsg.innerHTML = "Bd: " + status;
        return;
      }

      var p = JSON.parse(text);

      var key = topicId + "_" + departmentId;
      delete tipCache[key];

      currentCell.setAttribute("data-content", p.content || "");
      currentCell.setAttribute("data-version", String(p.version));

      var contentDiv = currentCell.getElementsByClassName("content")[0];
      var metaDiv = currentCell.getElementsByClassName("vmeta")[0];

      if (p.content && p.content.length) {
        contentDiv.style.color = "#000";
        contentDiv.innerHTML = escapeHtml(p.content);
      } else {
        contentDiv.style.color = "#999";
        contentDiv.innerHTML = "-";
      }
      metaDiv.innerHTML = "v" + p.version;

      setCellMeta(currentCell, p.last_changed_at, p.last_changed_by);

      modalMsg.style.color = "green";
      modalMsg.innerHTML = "Zapisano.";
      setTimeout(closeModal, 250);
    });
  };

  backdrop.onclick = function(e){
    if (e.target === backdrop) closeModal();
  };

  // -------- HOVER HISTORY TOOLTIP ----------
  var tipCache = {};

  function buildTipHtml(items) {
    if (!items || !items.length) {
      return "<div class='empty'>Brak historii (pierwszy wpis).</div>";
    }

    var html = "";
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      var meta = "v" + it.new_version + " • " + formatDate(it.changed_at) + " • user_id=" + it.changed_by;
      var content = (it.new_content && it.new_content.length) ? it.new_content : "(pusto)";

      html += "<div class='row'>"
        + "<div class='meta'>" + escapeHtml(meta) + "</div>"
        + "<div class='txt'>" + escapeHtml(content) + "</div>"
        + "</div>";
    }
    return html;
  }

  function showTip(cell) {
    var tip = cell.getElementsByClassName("tip")[0];
    if (!tip) return;
    tip.style.display = "block";
  }

  function hideTip(cell) {
    var tip = cell.getElementsByClassName("tip")[0];
    if (!tip) return;
    tip.style.display = "none";
  }

  function loadHistory(cell) {
    var topicId = cell.getAttribute("data-topic-id");
    var depId = cell.getAttribute("data-department-id");
    var key = topicId + "_" + depId;

    var tip = cell.getElementsByClassName("tip")[0];
    if (!tip) return;

    if (tipCache[key]) {
      tip.innerHTML = tipCache[key];
      showTip(cell);
      return;
    }

    tip.innerHTML = "<div class='empty'>adowanie historii...</div>";
    showTip(cell);

    xhr("GET", "/web/positions/history/by_cell/" + topicId + "/" + depId, null, null, function(status, text){
      if (status === 401) {
        tip.innerHTML = "<div class='empty'>Zaloguj si.</div>";
        return;
      }
      if (!(status >= 200 && status < 300)) {
        tip.innerHTML = "<div class='empty'>Bd: " + status + "</div>";
        return;
      }

      var items = [];
      try { items = text ? JSON.parse(text) : []; } catch(e) { items = []; }

      var html = buildTipHtml(items);
      tipCache[key] = html;
      tip.innerHTML = html;
    });
  }

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

    // ukryj tooltip przy prawym kliku
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
      delete tipCache[key];

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

      setCellMeta(cell, p.last_changed_at, p.last_changed_by);
    });
  }

  function bindCells() {
    var cells = document.getElementsByClassName("cell");
    for (var i=0; i<cells.length; i++) {
      (function(cell){
        cell.onclick = function(){ openModal(cell); };
        cell.onmouseenter = function(){ loadHistory(cell); };
        cell.onmouseleave = function(){ hideTip(cell); };

        cell.oncontextmenu = function(e){
          e.preventDefault();
          openContextMenu(cell, e.clientX, e.clientY);
          return false;
        };
      })(cells[i]);
    }
  }

  function initCellMeta() {
    var cells = document.getElementsByClassName("cell");
    for (var i=0; i<cells.length; i++) {
      (function(cell){
        var topicId = cell.getAttribute("data-topic-id");
        var depId = cell.getAttribute("data-department-id");
        xhr("GET", "/web/positions/by_cell/" + topicId + "/" + depId, null, null, function(status, text){
          if (!(status >= 200 && status < 300)) return;
          if (!text || text.trim().startsWith("<")) return;
          var p = null;
          try { p = JSON.parse(text); } catch(e) { p = null; }
          if (!p) return;
          setCellMeta(cell, p.last_changed_at, p.last_changed_by);
        });
      })(cells[i]);
    }
  }

  bindCells();
  initCellMeta();
})();
</script>

<!-- Context Menu (prawy klik) -->
<div id="ctxMenu" style="position:fixed; display:none; background:#111; color:#fff; border-radius:10px; padding:8px; z-index:9999; width:380px; box-shadow:0 10px 30px rgba(0,0,0,0.25);">
  <div id="ctxTitle" style="font-weight:600; margin-bottom:6px;">Historia</div>
  <div id="ctxItems"></div>
</div>

{% endblock %}
'''

path.write_text(prefix + new_tail, encoding="utf-8")
print("OK: Odbudowano poprawny ogon pliku (script + ctxMenu + endblock).")
print("Zapisano:", path)
